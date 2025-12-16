# 서버 수정 방법

## 문제 상황
카메라 점검 완료 후 결과가 전송되지 않고 WebSocket이 끊어집니다.
원인: `check_runner.py`의 datetime serialization 코드가 제대로 적용되지 않음

## 해결 방법

### 1. 서버에 접속
```bash
ssh koast-user@10.1.10.128
```

### 2. 파일 직접 수정
```bash
cd ~/edge-system-checker-web/backend/app/services
nano check_runner.py
```

### 3. `_save_to_db` 메서드 찾기
- `Ctrl + W`를 눌러 검색
- `def _save_to_db` 입력하여 검색

### 4. 다음 코드로 교체

**기존 코드 (약 231-263 라인):**
```python
async def _save_to_db(
    self,
    db: AsyncSession,
    check_type: str,
    result: Dict[str, Any],
    duration: float,
    camera_count: Optional[int] = None
):
    """점검 결과를 DB에 저장"""
    try:
        status = result.get('status', 'UNKNOWN')
        error_message = result.get('error') if status == 'ERROR' else None
        
        history = CheckHistory(
            check_type=check_type,
            status=status,
            results=result,
            error_message=error_message,
            duration_seconds=int(duration),
            camera_count=camera_count if check_type == 'camera' else None
        )
        
        db.add(history)
        await db.commit()
        await db.refresh(history)
        
        logger.info(f"점검 결과 저장 완료: {check_type} - {status}")
    except Exception as e:
        logger.error(f"점검 결과 저장 실패: {e}", exc_info=True)
        await db.rollback()
```

**새 코드 (datetime serialization 포함):**
```python
async def _save_to_db(
    self,
    db: AsyncSession,
    check_type: str,
    result: Dict[str, Any],
    duration: float,
    camera_count: Optional[int] = None
):
    """점검 결과를 DB에 저장"""
    try:
        # datetime 객체를 문자열로 변환하는 재귀 함수
        def serialize_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: serialize_datetime(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize_datetime(item) for item in obj]
            return obj
        
        # 결과를 JSON 직렬화 가능하게 변환
        serialized_result = serialize_datetime(result)
        
        status = serialized_result.get('status', 'UNKNOWN')
        error_message = serialized_result.get('error') if status == 'ERROR' else None
        
        history = CheckHistory(
            check_type=check_type,
            status=status,
            results=serialized_result,
            error_message=error_message,
            duration_seconds=int(duration),
            camera_count=camera_count if check_type == 'camera' else None
        )
        
        db.add(history)
        await db.commit()
        await db.refresh(history)
        
        logger.info(f"점검 결과 저장 완료: {check_type} - {status}")
    except Exception as e:
        logger.error(f"점검 결과 저장 실패: {e}", exc_info=True)
        await db.rollback()
```

### 5. 저장 및 종료
- `Ctrl + O` (저장)
- `Enter` (확인)
- `Ctrl + X` (종료)

### 6. 서버 재시작
```bash
cd ~/edge-system-checker-web/backend
source venv/bin/activate

# 기존 서버가 실행 중이면 Ctrl+C로 중지 후
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 7. 웹 브라우저에서 테스트
- `http://10.1.10.128:8000` 새로고침
- 점검 시작 버튼 클릭
- 진행률이 0% → 25% → 50% → 75% → 100%로 업데이트되는지 확인

