/**
 * REST API 클라이언트
 */
const API_BASE_URL = '/api';

class ApiClient {
    /**
     * 점검 실행
     */
    async runChecks(checks = null, cameraCount = 4, autoMode = true) {
        const response = await fetch(`${API_BASE_URL}/checks/run`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                checks: checks,
                camera_count: cameraCount,
                auto_mode: autoMode
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '점검 실행 실패');
        }
        
        return await response.json();
    }
    
    /**
     * 점검 상태 조회
     */
    async getCheckStatus() {
        const response = await fetch(`${API_BASE_URL}/checks/status`);
        if (!response.ok) {
            throw new Error('상태 조회 실패');
        }
        return await response.json();
    }
    
    /**
     * 점검 이력 조회
     */
    async getHistory(page = 1, pageSize = 20, checkType = null, status = null) {
        const params = new URLSearchParams({
            page: page.toString(),
            page_size: pageSize.toString()
        });
        
        if (checkType) params.append('check_type', checkType);
        if (status) params.append('status', status);
        
        const response = await fetch(`${API_BASE_URL}/history?${params}`);
        if (!response.ok) {
            throw new Error('이력 조회 실패');
        }
        return await response.json();
    }
    
    /**
     * 점검 이력 상세 조회
     */
    async getHistoryDetail(historyId) {
        const response = await fetch(`${API_BASE_URL}/history/${historyId}`);
        if (!response.ok) {
            throw new Error('이력 상세 조회 실패');
        }
        return await response.json();
    }
    
    /**
     * 설정 조회
     */
    async getConfig() {
        const response = await fetch(`${API_BASE_URL}/config`);
        if (!response.ok) {
            throw new Error('설정 조회 실패');
        }
        return await response.json();
    }
}

// 전역 인스턴스
const apiClient = new ApiClient();

