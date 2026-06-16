"""
F-01: 施策提案フロー

SCR-01 提案一覧        GET  /api/v1/proposals
SCR-02 提案生成        POST /api/v1/proposals          (SSE ストリーミング)
SCR-02 生成ストリーム  POST /api/v1/proposals/stream   (text/event-stream)
SCR-03 提案詳細        GET  /api/v1/proposals/{id}
SCR-04 再生成          POST /api/v1/proposals/{id}/regenerate  (DEC-022)
SCR-05 提出            POST /api/v1/proposals/{id}/submit
       署名付きURL     GET  /api/v1/proposals/{id}/content-url
"""
import asyncio
import json
import re
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import CurrentUser, require_roles
from app.core.database import get_db
from app.models.proposal import Proposal
from app.models.tenant import Tenant
from app.schemas.proposal import ContentUpdateRequest, DeepenRequest, ProposalCreate, ProposalDetail, ProposalRead, RefinementRequest
from app.services.claude import generate_deepen_streaming, generate_proposal, generate_proposal_streaming, generate_refine_streaming
from app.services.file_extractor import extract_text_from_file
from app.services.s3 import generate_presigned_url, upload_proposal_content
from app.services.url_fetcher import fetch_all

router = APIRouter(prefix="/proposals", tags=["proposals"])


# ---------------------------------------------------------------------------
# SCR-01 一覧
# ---------------------------------------------------------------------------
@router.get("/", response_model=list[ProposalRead])
async def list_proposals(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("consultant", "tl", "manager")),
):
    stmt = select(Proposal).order_by(Proposal.created_at.desc())
    if current_user.role == "consultant" and current_user.tenant_id:
        stmt = stmt.where(Proposal.tenant_id == current_user.tenant_id)
    result = await db.execute(stmt)
    return result.scalars().all()


# ---------------------------------------------------------------------------
# SCR-02 生成 (同期版 — 完全なレスポンスを返す)
# ---------------------------------------------------------------------------
@router.post("/", response_model=ProposalRead, status_code=status.HTTP_201_CREATED)
async def create_proposal(
    body: ProposalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("consultant")),
):
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="Consultant must be assigned to a tenant")

    tenant = await db.get(Tenant, current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # DB に先に draft レコードを作成して ID を確定させる
    proposal = Proposal(
        tenant_id=current_user.tenant_id,
        created_by=current_user.user_id,
        municipality_name=tenant.municipality_name,
        theme=body.theme,
        status="draft",
    )
    db.add(proposal)
    await db.flush()

    # Claude API で生成 → S3 アップロード
    content = await generate_proposal(tenant.municipality_name, body.theme)
    content_url = await asyncio.get_event_loop().run_in_executor(
        None, upload_proposal_content, proposal.id, content
    )
    proposal.content_url = content_url

    await db.commit()
    await db.refresh(proposal)
    return proposal


# ---------------------------------------------------------------------------
# SCR-02 生成 (SSEストリーミング版) — フロントエンドのリアルタイム表示用
# ---------------------------------------------------------------------------
@router.post("/stream")
async def stream_proposal(
    future_vision: str = Form(...),
    current_state: str = Form(default=""),
    challenges: str = Form(default=""),
    root_causes: str = Form(default=""),
    reference_urls: list[str] = Form(default=[]),
    attachments: list[UploadFile] = File(default=[]),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("consultant")),
):
    """
    multipart/form-data で構造化入力 + ファイルを受け取り、
    text/event-stream で Claude の生成テキストをリアルタイム送信。
    最後の event: done で proposal_id を通知。
    """
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="Consultant must be assigned to a tenant")

    tenant = await db.get(Tenant, current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # 添付ファイルのテキスト抽出（PDF / Word / Excel / PPT / テキスト系）
    attachment_texts: list[tuple[str, str]] = []
    for f in attachments:
        raw = await f.read()
        text = extract_text_from_file(f.filename or "unnamed", raw)
        attachment_texts.append((f.filename or "unnamed", text))

    # 参照URLのコンテンツ取得（Google Drive / Sheets / 一般Webページ）
    url_contents: list[tuple[str, str]] = await fetch_all(reference_urls)

    proposal = Proposal(
        tenant_id=current_user.tenant_id,
        created_by=current_user.user_id,
        municipality_name=tenant.municipality_name,
        theme=future_vision[:200],
        status="draft",
        # 入力内容を保存（ワークスペース表示・再利用用）
        future_vision=future_vision,
        current_state=current_state,
        challenges=challenges,
        root_causes=root_causes,
        reference_urls=json.dumps(
            [u for u in reference_urls if u.strip()], ensure_ascii=False
        ),
        attachment_names=json.dumps(
            [f.filename for f in attachments if f.filename], ensure_ascii=False
        ),
    )
    db.add(proposal)
    await db.flush()
    await db.commit()
    await db.refresh(proposal)

    proposal_id = proposal.id

    async def event_generator():
        full_text = []
        async for chunk in generate_proposal_streaming(
            municipality_name=tenant.municipality_name,
            future_vision=future_vision,
            current_state=current_state,
            challenges=challenges,
            root_causes=root_causes,
            url_contents=url_contents,
            attachment_texts=attachment_texts,
        ):
            full_text.append(chunk)
            yield f"data: {chunk.replace(chr(10), '<br>')}\n\n"

        content = "".join(full_text)
        content_url = await asyncio.get_event_loop().run_in_executor(
            None, upload_proposal_content, proposal_id, content
        )

        async with db.begin_nested():
            p = await db.get(Proposal, proposal_id)
            if p:
                p.content_url = content_url
                p.content_text = content  # DB にも保存して直接編集を可能にする
        await db.commit()

        # 生成テキストから施策一覧を抽出して SSE で送信
        measures = _extract_measures(content)
        if measures:
            yield f"event: measures\ndata: {json.dumps(measures, ensure_ascii=False)}\n\n"

        yield f"event: done\ndata: {proposal_id}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def _extract_measures(text: str) -> list[dict]:
    """テキスト中の ①〜⑩ を含む表行から施策一覧を抽出する。"""
    circle_map = "①②③④⑤⑥⑦⑧⑨⑩"
    measures: list[dict] = []
    seen: set[int] = set()
    for m in re.finditer(r"\|\s*([①②③④⑤⑥⑦⑧⑨⑩])\s*\|\s*([^|]+?)\s*\|", text):
        circle = m.group(1)
        title = m.group(2).strip()
        idx = circle_map.index(circle) + 1
        if idx not in seen:
            seen.add(idx)
            measures.append({"index": idx, "title": title})
    return measures


# ---------------------------------------------------------------------------
# 採用施策の深掘り (SSE ストリーミング)
# ---------------------------------------------------------------------------
@router.post("/{proposal_id}/deepen")
async def deepen_proposal(
    proposal_id: uuid.UUID,
    body: DeepenRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("consultant")),
):
    """選択された施策の詳細実施計画をストリーミングで生成する。"""
    proposal = await db.get(Proposal, proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    if str(proposal.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")

    selected = [(m.index, m.title) for m in body.selected_measures]

    async def event_generator():
        full_text = []
        async for chunk in generate_deepen_streaming(
            municipality_name=proposal.municipality_name,
            selected_measures=selected,
            future_vision=body.future_vision or proposal.theme,
        ):
            full_text.append(chunk)
            yield f"data: {chunk.replace(chr(10), '<br>')}\n\n"

        # 深掘り内容を S3 に保存して content_url を更新
        content = "".join(full_text)
        content_url = await asyncio.get_event_loop().run_in_executor(
            None, upload_proposal_content, proposal_id, content
        )
        async with db.begin_nested():
            p = await db.get(Proposal, proposal_id)
            if p:
                p.content_url = content_url
                p.content_text = content  # DB にも保存して直接編集を可能にする
        await db.commit()

        yield f"event: done\ndata: {proposal_id}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# 精緻化（追加指示 → 新バージョン生成）
# ---------------------------------------------------------------------------
@router.post("/{proposal_id}/refine")
async def refine_proposal(
    proposal_id: uuid.UUID,
    body: RefinementRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("consultant")),
):
    """追加指示でこのバージョンを元に新バージョンを生成する。SSEストリーミング。"""
    parent = await db.get(Proposal, proposal_id)
    if not parent:
        raise HTTPException(status_code=404, detail="Proposal not found")
    if str(parent.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")

    # 親を superseded に
    parent.status = "superseded"

    # 入力情報を引き継ぎ
    new_proposal = Proposal(
        tenant_id=parent.tenant_id,
        created_by=current_user.user_id,
        municipality_name=parent.municipality_name,
        theme=parent.theme,
        parent_proposal_id=parent.id,
        status="draft",
        future_vision=parent.future_vision or parent.theme,
        current_state=parent.current_state,
        challenges=parent.challenges,
        root_causes=parent.root_causes,
        reference_urls=parent.reference_urls,
        attachment_names=parent.attachment_names,
        refine_instruction=body.instruction,
    )
    db.add(new_proposal)
    await db.flush()
    await db.commit()
    await db.refresh(new_proposal)

    new_id = new_proposal.id

    async def event_generator():
        full_text = []
        async for chunk in generate_refine_streaming(
            municipality_name=parent.municipality_name,
            instruction=body.instruction,
            current_content=parent.content_text or "",
            future_vision=parent.future_vision or parent.theme,
            current_state=parent.current_state or "",
            challenges=parent.challenges or "",
            root_causes=parent.root_causes or "",
        ):
            full_text.append(chunk)
            yield f"data: {chunk.replace(chr(10), '<br>')}\n\n"

        content = "".join(full_text)
        content_url = await asyncio.get_event_loop().run_in_executor(
            None, upload_proposal_content, new_id, content
        )
        async with db.begin_nested():
            p = await db.get(Proposal, new_id)
            if p:
                p.content_url = content_url
                p.content_text = content
        await db.commit()

        measures = _extract_measures(content)
        if measures:
            yield f"event: measures\ndata: {json.dumps(measures, ensure_ascii=False)}\n\n"

        yield f"event: done\ndata: {new_id}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# 提案チェーン取得（ルートから最新まで）
# ---------------------------------------------------------------------------
@router.get("/{proposal_id}/chain", response_model=list[ProposalRead])
async def get_proposal_chain(
    proposal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("consultant", "tl", "manager")),
):
    """このプロポーザルを末尾にした世代チェーンをルートから順に返す。"""
    chain: list[Proposal] = []
    current_id: uuid.UUID | None = proposal_id
    while current_id:
        p = await db.get(Proposal, current_id)
        if not p:
            break
        if current_user.role == "consultant" and str(p.tenant_id) != str(current_user.tenant_id):
            raise HTTPException(status_code=403, detail="Forbidden")
        chain.insert(0, p)
        current_id = p.parent_proposal_id
    return chain


# ---------------------------------------------------------------------------
# SCR-03 詳細
# ---------------------------------------------------------------------------
@router.get("/{proposal_id}", response_model=ProposalDetail)
async def get_proposal(
    proposal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("consultant", "tl", "manager")),
):
    proposal = await db.get(
        Proposal,
        proposal_id,
        options=[selectinload(Proposal.evidence)],
    )
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    if current_user.role == "consultant" and str(proposal.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    return proposal


# ---------------------------------------------------------------------------
# 提案書本文テキストの取得・更新 (直接編集用)
# ---------------------------------------------------------------------------
@router.get("/{proposal_id}/text")
async def get_proposal_text(
    proposal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("consultant", "tl", "manager")),
):
    proposal = await db.get(Proposal, proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    if current_user.role == "consultant" and str(proposal.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    return {"content_text": proposal.content_text or ""}


@router.put("/{proposal_id}/content", response_model=ProposalRead)
async def update_proposal_content(
    proposal_id: uuid.UUID,
    body: ContentUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("consultant")),
):
    """提案書本文を直接編集して保存する。draft のみ更新可。"""
    proposal = await db.get(Proposal, proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    if proposal.status not in ("draft", "rejected"):
        raise HTTPException(status_code=409, detail="Only draft/rejected proposals can be edited")
    if str(proposal.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")

    proposal.content_text = body.content_text
    # S3 も更新（デモでは fake URL になるが形式を保つ）
    content_url = await asyncio.get_event_loop().run_in_executor(
        None, upload_proposal_content, proposal_id, body.content_text
    )
    proposal.content_url = content_url
    await db.commit()
    await db.refresh(proposal)
    return proposal


# ---------------------------------------------------------------------------
# 提案書本文の署名付き URL を返す (S3 presigned URL)
# ---------------------------------------------------------------------------
@router.get("/{proposal_id}/content-url")
async def get_content_url(
    proposal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("consultant", "tl", "manager")),
):
    proposal = await db.get(Proposal, proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    if current_user.role == "consultant" and str(proposal.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    if not proposal.content_url:
        raise HTTPException(status_code=404, detail="Content not available yet")

    presigned = await asyncio.get_event_loop().run_in_executor(
        None, generate_presigned_url, proposal.content_url
    )
    return {"url": presigned}


# ---------------------------------------------------------------------------
# SCR-04 再生成 (DEC-022)
# ---------------------------------------------------------------------------
@router.post("/{proposal_id}/regenerate", response_model=ProposalRead, status_code=status.HTTP_201_CREATED)
async def regenerate_proposal(
    proposal_id: uuid.UUID,
    body: ProposalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("consultant")),
):
    """DEC-022: 新規 ID レコードを作成し、旧 draft を superseded に更新する。"""
    old = await db.get(Proposal, proposal_id)
    if not old:
        raise HTTPException(status_code=404, detail="Proposal not found")
    if old.status != "draft":
        raise HTTPException(status_code=409, detail="Only draft proposals can be regenerated")
    if str(old.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")

    tenant = await db.get(Tenant, current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    old.status = "superseded"

    new_proposal = Proposal(
        tenant_id=current_user.tenant_id,
        parent_proposal_id=old.id,
        created_by=current_user.user_id,
        municipality_name=tenant.municipality_name,
        theme=body.theme,
        status="draft",
    )
    db.add(new_proposal)
    await db.flush()

    content = await generate_proposal(tenant.municipality_name, body.theme)
    content_url = await asyncio.get_event_loop().run_in_executor(
        None, upload_proposal_content, new_proposal.id, content
    )
    new_proposal.content_url = content_url

    await db.commit()
    await db.refresh(new_proposal)
    return new_proposal


# ---------------------------------------------------------------------------
# SCR-05 提出
# ---------------------------------------------------------------------------
@router.post("/{proposal_id}/submit", response_model=ProposalRead)
async def submit_proposal(
    proposal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("consultant")),
):
    proposal = await db.get(Proposal, proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    if proposal.status != "draft":
        raise HTTPException(status_code=409, detail="Only draft proposals can be submitted")
    if str(proposal.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")

    proposal.status = "reviewing_tl"
    await db.commit()
    await db.refresh(proposal)
    return proposal
