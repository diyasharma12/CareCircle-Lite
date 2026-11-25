import json
import time

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import assistant, crud, models, schemas
from app.database import get_db
from app.timeutils import utcnow

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/ask")
def ask(payload: schemas.AskRequest, db: Session = Depends(get_db)):
    recipient = db.get(models.CareRecipient, payload.recipient_id)
    if recipient is None:
        raise HTTPException(status_code=404, detail="Recipient not found")

    grouping = crud.get_today_grouping(db, payload.recipient_id, now=utcnow())
    context = assistant.build_context(recipient.name, grouping)

    async def event_stream():
        started = time.perf_counter()
        collected: list[str] = []
        try:
            async for chunk in assistant.stream_answer(payload.question, context):
                collected.append(chunk)
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        finally:
            latency_ms = int((time.perf_counter() - started) * 1000)
            full_answer = "".join(collected)
            # New session so this still commits even if the client disconnected mid-stream.
            from app.database import SessionLocal

            log_db = SessionLocal()
            try:
                crud.log_ai_interaction(
                    log_db,
                    recipient_id=payload.recipient_id,
                    question=payload.question,
                    context=json.dumps(context),
                    answer=full_answer,
                    latency_ms=latency_ms,
                )
            finally:
                log_db.close()
            yield f"data: {json.dumps({'done': True, 'latency_ms': latency_ms})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/logs", response_model=list[schemas.AIInteractionOut])
def list_logs(db: Session = Depends(get_db)):
    return list(db.query(models.AIInteraction).order_by(models.AIInteraction.created_at.desc()))
