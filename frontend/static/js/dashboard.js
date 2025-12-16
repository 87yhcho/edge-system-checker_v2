/**
 * 대시보드 메인 로직
 */
class Dashboard {
    constructor() {
        this.isRunning = false;
        this.currentResults = {};
        this.init();
    }
    
    /**
     * 초기화
     */
    init() {
        // WebSocket 이벤트 리스너 등록
        wsClient.on('connect', () => {
            this.updateConnectionStatus(true);
        });
        
        wsClient.on('disconnect', () => {
            this.updateConnectionStatus(false);
        });
        
        wsClient.on('progress', (data) => {
            this.handleProgress(data);
        });
        
        wsClient.on('result', (data) => {
            this.handleResult(data);
        });
        
        wsClient.on('error', (data) => {
            this.handleError(data);
        });
        
        // WebSocket 연결
        wsClient.connect();
        
        // 버튼 이벤트 등록
        document.getElementById('runChecksBtn').addEventListener('click', () => {
            this.runChecks();
        });
        
        // 주기적으로 상태 확인
        setInterval(() => {
            this.updateStatus();
        }, 2000);
        
        // 초기 상태 업데이트
        this.updateStatus();
        this.loadHistory();
    }
    
    /**
     * 점검 실행
     */
    async runChecks() {
        if (this.isRunning) {
            alert('점검이 이미 실행 중입니다.');
            return;
        }
        
        const cameraCount = parseInt(document.getElementById('cameraCount').value) || 4;
        const autoMode = document.getElementById('autoMode').checked;
        const selectedChecks = this.getSelectedChecks();
        
        try {
            this.isRunning = true;
            this.updateRunButton(false);
            this.clearResults();
            
            await apiClient.runChecks(selectedChecks, cameraCount, autoMode);
            
            // 상태는 WebSocket으로 업데이트됨
        } catch (error) {
            alert(`점검 실행 실패: ${error.message}`);
            this.isRunning = false;
            this.updateRunButton(true);
        }
    }
    
    /**
     * 선택된 점검 항목 가져오기
     */
    getSelectedChecks() {
        const checks = [];
        if (document.getElementById('checkUps').checked) checks.push('ups');
        if (document.getElementById('checkCamera').checked) checks.push('camera');
        if (document.getElementById('checkNas').checked) checks.push('nas');
        if (document.getElementById('checkSystem').checked) checks.push('system');
        return checks.length > 0 ? checks : null;
    }
    
    /**
     * 진행 상황 처리
     */
    handleProgress(data) {
        const { checkType, progress, message, status } = data;
        
        console.log('Progress update:', JSON.stringify(data));  // 디버그용 - 전체 데이터 출력
        console.log(`  checkType: ${checkType}, progress: ${progress}, message: ${message}, status: ${status}`);
        
        // 진행률 바 업데이트
        if (checkType === 'all') {
            const progressBar = document.getElementById('overallProgress');
            if (progressBar) {
                progressBar.style.width = `${progress}%`;
                progressBar.setAttribute('aria-valuenow', progress);
                progressBar.textContent = `${progress}%`;
            }
        }
        
        // 메시지 표시
        const messageDiv = document.getElementById('statusMessage');
        if (messageDiv) {
            messageDiv.textContent = message;
            messageDiv.className = `alert alert-${status === 'running' ? 'info' : status === 'completed' ? 'success' : 'warning'}`;
            messageDiv.style.display = 'block';
        }
        
        // 개별 체크 타입별 카드 업데이트 (진행 중 표시)
        if (checkType !== 'all') {
            const card = document.getElementById(`${checkType}Card`);
            if (card) {
                const detailsDiv = card.querySelector('.check-details');
                if (detailsDiv && status === 'running') {
                    detailsDiv.innerHTML = `<div class="spinner-border spinner-border-sm" role="status"></div> <small>${message}</small>`;
                }
            }
        }
    }
    
    /**
     * 결과 처리
     */
    handleResult(data) {
        const { checkType, result } = data;
        
        console.log('Result received:', JSON.stringify(data));  // 디버그용
        console.log(`  checkType: ${checkType}, status: ${result?.status}`);
        
        this.currentResults[checkType] = result;
        this.updateCheckCard(checkType, result);
        
        // 전체 점검 완료 시
        if (checkType === 'all') {
            this.isRunning = false;
            this.updateRunButton(true);
            this.loadHistory();
        }
    }
    
    /**
     * 오류 처리
     */
    handleError(data) {
        const { checkType, error } = data;
        
        const card = document.getElementById(`${checkType}Card`);
        if (card) {
            card.classList.remove('border-success', 'border-danger', 'border-warning');
            card.classList.add('border-danger');
            
            const statusBadge = card.querySelector('.status-badge');
            if (statusBadge) {
                statusBadge.textContent = 'ERROR';
                statusBadge.className = 'badge bg-danger status-badge';
            }
        }
        
        alert(`점검 오류 (${checkType}): ${error}`);
    }
    
    /**
     * 점검 카드 업데이트
     */
    updateCheckCard(checkType, result) {
        const card = document.getElementById(`${checkType}Card`);
        if (!card) return;
        
        const status = result.status || 'UNKNOWN';
        const statusBadge = card.querySelector('.status-badge');
        
        // 카드 스타일 업데이트
        card.classList.remove('border-success', 'border-danger', 'border-warning');
        if (status === 'PASS') {
            card.classList.add('border-success');
            if (statusBadge) {
                statusBadge.textContent = 'PASS';
                statusBadge.className = 'badge bg-success status-badge';
            }
        } else if (status === 'FAIL' || status === 'ERROR') {
            card.classList.add('border-danger');
            if (statusBadge) {
                statusBadge.textContent = status;
                statusBadge.className = 'badge bg-danger status-badge';
            }
        } else {
            card.classList.add('border-warning');
            if (statusBadge) {
                statusBadge.textContent = status;
                statusBadge.className = 'badge bg-warning status-badge';
            }
        }
        
        // 상세 정보 업데이트
        const detailsDiv = card.querySelector('.check-details');
        if (detailsDiv) {
            detailsDiv.innerHTML = this.formatCheckDetails(result);
        }
    }
    
    /**
     * 점검 상세 정보 포맷
     */
    formatCheckDetails(result) {
        if (!result || typeof result !== 'object') return '';
        
        let html = '<div class="small">';
        
        // 카메라 점검인 경우
        if (result.details && Array.isArray(result.details)) {
            html += '<strong>카메라 상세:</strong><ul class="list-unstyled mb-0 mt-1">';
            result.details.forEach(detail => {
                const sourceStatus = detail.source_status || 'UNKNOWN';
                const blurStatus = detail.mediamtx_status || 'UNKNOWN';
                const logStatus = detail.log_status || 'UNKNOWN';
                
                const sourceIcon = sourceStatus === 'PASS' ? '✓' : sourceStatus === 'FAIL' ? '✗' : '?';
                const blurIcon = blurStatus === 'PASS' ? '✓' : blurStatus === 'FAIL' ? '✗' : '?';
                const logIcon = logStatus === 'PASS' ? '✓' : logStatus === 'FAIL' ? '✗' : '?';
                
                html += `<li class="mb-1">${detail.name || 'N/A'} (${detail.ip || 'N/A'})`;
                html += `<br>&nbsp;&nbsp;<small>원본:${sourceIcon} 블러:${blurIcon} 로그:${logIcon}</small></li>`;
            });
            html += '</ul>';
        }
        
        // UPS 점검인 경우
        else if (result.services || result.ups_data) {
            if (result.services && result.services.all_active !== undefined) {
                html += `<strong>서비스:</strong> ${result.services.all_active ? '✓ 정상' : '✗ 오류'}<br>`;
            }
            if (result.ups_data && result.ups_data.data) {
                html += `<strong>UPS 상태:</strong> ${result.ups_data.data['ups.status'] || 'N/A'}<br>`;
                html += `<strong>배터리:</strong> ${result.ups_data.data['battery.charge'] || 'N/A'}%<br>`;
            }
        }
        
        // NAS 점검인 경우
        else if (result.ssh_connected !== undefined) {
            html += `<strong>SSH 연결:</strong> ${result.ssh_connected ? '✓ 성공' : '✗ 실패'}<br>`;
            if (result.disk_usage) {
                html += `<strong>디스크:</strong> 확인됨<br>`;
            }
        }
        
        // 시스템 점검인 경우
        else if (result.summary) {
            const summary = result.summary;
            html += `<strong>통계:</strong> `;
            html += `<span class="text-success">✓${summary.pass_count || 0}</span> `;
            html += `<span class="text-danger">✗${summary.fail_count || 0}</span> `;
            html += `<span class="text-warning">⚠${summary.warn_count || 0}</span> `;
            html += `<span class="text-muted">◌${summary.skip_count || 0}</span><br>`;
            
            if (summary.failed_items && summary.failed_items.length > 0) {
                html += `<strong class="text-danger">실패 항목:</strong><br>`;
                html += `<small>${summary.failed_items.join(', ')}</small><br>`;
            }
        }
        
        html += '</div>';
        return html || '<small class="text-muted">대기 중...</small>';
    }
    
    /**
     * 결과 초기화
     */
    clearResults() {
        this.currentResults = {};
        const cards = document.querySelectorAll('.check-card');
        cards.forEach(card => {
            card.classList.remove('border-success', 'border-danger', 'border-warning');
            const statusBadge = card.querySelector('.status-badge');
            if (statusBadge) {
                statusBadge.textContent = '-';
                statusBadge.className = 'badge bg-secondary status-badge';
            }
        });
        
        const progressBar = document.getElementById('overallProgress');
        progressBar.style.width = '0%';
        progressBar.setAttribute('aria-valuenow', 0);
        progressBar.textContent = '0%';
    }
    
    /**
     * 실행 버튼 업데이트
     */
    updateRunButton(enabled) {
        const btn = document.getElementById('runChecksBtn');
        btn.disabled = !enabled;
        btn.textContent = enabled ? '점검 시작' : '점검 실행 중...';
    }
    
    /**
     * 연결 상태 업데이트
     */
    updateConnectionStatus(connected) {
        const statusDiv = document.getElementById('connectionStatus');
        if (statusDiv) {
            statusDiv.textContent = connected ? '연결됨' : '연결 안 됨';
            statusDiv.className = connected ? 'badge bg-success' : 'badge bg-danger';
        }
    }
    
    /**
     * 상태 업데이트
     */
    async updateStatus() {
        try {
            const status = await apiClient.getCheckStatus();
            this.isRunning = status.is_running;
            
            if (status.is_running) {
                this.updateRunButton(false);
            } else {
                this.updateRunButton(true);
            }
        } catch (error) {
            console.error('상태 업데이트 실패:', error);
        }
    }
    
    /**
     * 이력 로드
     */
    async loadHistory() {
        try {
            const history = await apiClient.getHistory(1, 5);
            this.displayHistory(history.items);
        } catch (error) {
            console.error('이력 로드 실패:', error);
        }
    }
    
    /**
     * 이력 표시
     */
    displayHistory(items) {
        const historyDiv = document.getElementById('recentHistory');
        if (!historyDiv) return;
        
        if (items.length === 0) {
            historyDiv.innerHTML = '<p class="text-muted">이력이 없습니다.</p>';
            return;
        }
        
        let html = '<ul class="list-group list-group-flush">';
        items.forEach(item => {
            const statusClass = item.status === 'PASS' ? 'success' : 
                              item.status === 'FAIL' ? 'danger' : 'warning';
            const date = new Date(item.timestamp).toLocaleString('ko-KR');
            html += `
                <li class="list-group-item">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong>${item.check_type.toUpperCase()}</strong>
                            <small class="text-muted ms-2">${date}</small>
                        </div>
                        <span class="badge bg-${statusClass}">${item.status}</span>
                    </div>
                </li>
            `;
        });
        html += '</ul>';
        
        historyDiv.innerHTML = html;
    }
}

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', () => {
    new Dashboard();
});

