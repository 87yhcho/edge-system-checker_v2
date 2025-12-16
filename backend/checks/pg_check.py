"""
PostgreSQL 데이터 수신 점검 모듈
데이터베이스 연결 및 데이터 조회
"""
import psycopg2
from typing import Dict, Any, List


def test_pg_connection(host: str, port: int, db: str, user: str, password: str) -> Dict[str, Any]:
    """PostgreSQL 연결 테스트"""
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=db,
            user=user,
            password=password,
            connect_timeout=5
        )
        conn.close()
        return {
            'success': True,
            'message': 'Connection successful'
        }
    except psycopg2.OperationalError as e:
        return {
            'success': False,
            'error': f'Connection failed: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }


def query_table_data(
    host: str,
    port: int,
    db: str,
    user: str,
    password: str,
    table: str,
    limit: int = 5
) -> Dict[str, Any]:
    """테이블에서 최근 데이터 조회"""
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=db,
            user=user,
            password=password,
            connect_timeout=5
        )
        cur = conn.cursor()
        
        # 테이블 존재 여부 확인
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            )
        """, (table,))
        table_exists = cur.fetchone()[0]
        
        if not table_exists:
            conn.close()
            return {
                'success': False,
                'error': f"Table '{table}' does not exist"
            }
        
        # 데이터 조회 (최근 데이터 가져오기)
        # ORDER BY 절이 없으면 테이블 스캔 순서로 가져옴
        try:
            cur.execute(f"SELECT * FROM {table} ORDER BY 1 DESC LIMIT %s", (limit,))
        except:
            # ORDER BY 실패 시 그냥 LIMIT만 사용
            cur.execute(f"SELECT * FROM {table} LIMIT %s", (limit,))
        
        cols = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        
        # 데이터를 딕셔너리 리스트로 변환
        data = []
        for row in rows:
            row_dict = {}
            for i, col in enumerate(cols):
                value = row[i]
                # 데이터 타입에 따라 문자열로 변환
                if value is None:
                    row_dict[col] = 'NULL'
                else:
                    row_dict[col] = str(value)
            data.append(row_dict)
        
        # 행 개수 조회
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        total_rows = cur.fetchone()[0]
        
        conn.close()
        
        return {
            'success': True,
            'columns': cols,
            'data': data,
            'row_count': len(rows),
            'total_rows': total_rows
        }
    
    except psycopg2.Error as e:
        return {
            'success': False,
            'error': f'Query failed: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }


def check_postgresql(pg_config: Dict[str, str], table_name: str = None) -> Dict[str, Any]:
    """전체 PostgreSQL 점검 실행"""
    from utils.ui import (
        print_section, print_pass, print_fail, print_info,
        print_warning, print_table, ask_input
    )
    
    print_section(3, 4, "PostgreSQL 데이터 수신 점검")
    
    # 설정 정보
    host = pg_config.get('host', 'localhost')
    port = int(pg_config.get('port', 5432))
    db = pg_config.get('db', 'postgres')
    user = pg_config.get('user', 'postgres')
    password = pg_config.get('password', '')
    
    print_info(f"연결 정보: {user}@{host}:{port}/{db}")
    
    result = {
        'status': 'UNKNOWN',
        'connection': 'Not tested',
        'table': table_name,
        'row_count': 0,
        'sample_data': []
    }
    
    # 1. 연결 테스트
    print_info("PostgreSQL 연결 테스트 중...")
    conn_result = test_pg_connection(host, port, db, user, password)
    
    if not conn_result['success']:
        print_fail(f"연결 실패: {conn_result['error']}")
        result['status'] = 'FAIL'
        result['connection'] = 'Failed'
        result['error'] = conn_result['error']
        return result
    
    print_pass("PostgreSQL 연결 성공")
    result['connection'] = 'Success'
    
    # 2. 테이블명 입력 받기
    if not table_name:
        print("")
        table_name = ask_input("조회할 테이블명을 입력하세요", "data")
        result['table'] = table_name
    
    if not table_name:
        print_warning("테이블명이 입력되지 않았습니다.")
        result['status'] = 'SKIP'
        return result
    
    # 3. 데이터 조회
    print("")
    print_info(f"테이블 '{table_name}'에서 데이터 조회 중...")
    query_result = query_table_data(host, port, db, user, password, table_name, limit=5)
    
    if not query_result['success']:
        print_fail(f"데이터 조회 실패: {query_result['error']}")
        result['status'] = 'FAIL'
        result['error'] = query_result['error']
        return result
    
    # 결과 출력
    row_count = query_result['row_count']
    total_rows = query_result['total_rows']
    
    print_pass(f"데이터 조회 성공 (총 {total_rows}건, 샘플 {row_count}건)")
    result['row_count'] = row_count
    result['total_rows'] = total_rows
    result['sample_data'] = query_result['data']
    
    if row_count > 0:
        print("")
        print_info(f"최근 데이터 샘플 (최대 {row_count}건):")
        
        # 데이터를 테이블로 출력
        columns = query_result['columns']
        data = query_result['data']
        
        # 컬럼이 너무 많으면 일부만 표시
        max_cols = 8
        if len(columns) > max_cols:
            print_warning(f"컬럼이 {len(columns)}개로 많습니다. 처음 {max_cols}개만 표시합니다.")
            display_cols = columns[:max_cols]
        else:
            display_cols = columns
        
        # 테이블 데이터 준비
        rows = []
        for item in data:
            row = []
            for col in display_cols:
                value = item.get(col, '')
                # 값이 너무 길면 자르기
                if len(value) > 30:
                    value = value[:27] + '...'
                row.append(value)
            rows.append(row)
        
        print_table(display_cols, rows)
        
        # 전체 상태 판정
        print("")
        result['status'] = 'PASS'
        print_pass("PostgreSQL 점검 결과: PASS")
    else:
        print_warning("테이블에 데이터가 없습니다.")
        result['status'] = 'FAIL'
        print_fail("PostgreSQL 점검 결과: FAIL (데이터 없음)")
    
    return result

