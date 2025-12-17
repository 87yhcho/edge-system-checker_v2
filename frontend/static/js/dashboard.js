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
        
        // 페이지 로드 시 진행 중인 점검 상태 복원
        this.restoreCheckState();
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
        
        // 디버깅: result 구조 출력
        console.log('formatCheckDetails - result:', JSON.stringify(result, null, 2));
        
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
        
        // UPS 점검인 경우 (ups_data가 있거나 services의 값이 문자열인 경우)
        else if (result.ups_data || (result.services && !result.summary)) {
            if (result.services && typeof Object.values(result.services)[0] === 'string') {
                const activeCount = Object.values(result.services).filter(v => v === 'active').length;
                const totalCount = Object.keys(result.services).length;
                html += `<strong>서비스:</strong> ${activeCount === totalCount ? '✓' : '✗'} ${activeCount}/${totalCount} 활성<br>`;
            }
            if (result.ups_data && result.ups_data.data) {
                html += `<strong>UPS 상태:</strong> ${result.ups_data.data['ups.status'] || 'N/A'}<br>`;
                html += `<strong>배터리:</strong> ${result.ups_data.data['battery.charge'] || 'N/A'}%<br>`;
            }
        }
        
        // NAS 점검인 경우 (실제 데이터 구조에 맞춤)
        else if (result.connection !== undefined || result.storage) {
            console.log('NAS 점검 감지:', result);
            
            // 연결 상태
            if (result.connection) {
                const isConnected = result.connection === 'Success';
                html += `<strong>SSH:</strong> ${isConnected ? '✓ 성공' : '✗ 실패'}`;
                if (result.connected_port) {
                    html += ` (포트 ${result.connected_port})`;
                }
                html += `<br>`;
            }
            
            // 시스템 정보
            if (result.system && result.system.hostname) {
                html += `<strong>호스트:</strong> ${result.system.hostname}<br>`;
            }
            
            // RAID 정보
            if (result.storage && result.storage.raid_info) {
                const raidInfo = result.storage.raid_info;
                const md2 = raidInfo.md2; // 데이터 볼륨
                if (md2) {
                    const raidOk = md2.status && !md2.status.includes('_');
                    html += `<strong>RAID:</strong> ${raidOk ? '✓' : '✗'} ${md2.level.toUpperCase()} `;
                    html += `(${md2.active}/${md2.disk_count} 디스크, ${Math.round(md2.capacity_gb)}TB)<br>`;
                }
            }
            
            // 디스크 사용량 (disk_usage 문자열 파싱)
            if (result.storage && result.storage.disk_usage) {
                const lines = result.storage.disk_usage.split('\n');
                const volumeLine = lines.find(line => line.includes('/volume1'));
                if (volumeLine) {
                    const parts = volumeLine.trim().split(/\s+/);
                    if (parts.length >= 5) {
                        html += `<strong>Volume1:</strong> ${parts[4]} 사용 (${parts[2]}/${parts[1]})<br>`;
                    }
                }
            }
        }
        
        // 시스템 점검인 경우 (실제 데이터 구조에 맞춤)
        else if (result.summary || result.setup_scripts || result.tomcat_details) {
            console.log('시스템 점검 감지:', result);
            
            // 통계 정보
            if (result.summary) {
                const summary = result.summary;
                html += `<strong>통계:</strong> `;
                html += `<span class="text-success">✓${summary.pass_count || 0}</span> `;
                html += `<span class="text-danger">✗${summary.fail_count || 0}</span> `;
                html += `<span class="text-warning">⚠${summary.warn_count || 0}</span> `;
                html += `<span class="text-muted">◌${summary.skip_count || 0}</span><br>`;
            }
            
            // 주요 서비스 상태 (services 객체 구조가 중첩됨)
            if (result.services) {
                const services = result.services;
                html += `<strong>서비스:</strong> `;
                const serviceNames = ['tomcat', 'postgresql', 'nut-server', 'nut-monitor', 'stream'];
                const serviceStatus = [];
                serviceNames.forEach(svc => {
                    if (services[svc] && services[svc].state) {
                        const isActive = services[svc].state === 'active';
                        const icon = isActive ? '✓' : '✗';
                        serviceStatus.push(icon + svc.replace('nut-', ''));
                    }
                });
                html += `${serviceStatus.slice(0, 3).join(' ')}`;
                if (serviceStatus.length > 3) {
                    html += ` 외 ${serviceStatus.length - 3}개`;
                }
                html += `<br>`;
            }
            
            // 실패/경고 항목 표시
            if (result.setup_scripts) {
                const scripts = result.setup_scripts;
                const failedItems = [];
                const warnItems = [];
                
                Object.keys(scripts).forEach(key => {
                    if (scripts[key].status === 'FAIL') {
                        failedItems.push(scripts[key].value || key.replace(/_/g, ' '));
                    } else if (scripts[key].status === 'WARN') {
                        warnItems.push(key.replace(/^(post_install_|nut_setup_)/, '').replace(/_/g, ' '));
                    }
                });
                
                if (failedItems.length > 0) {
                    html += `<strong class="text-danger">실패:</strong> <small>${failedItems[0].substring(0, 30)}...</small><br>`;
                }
                
                if (warnItems.length > 0) {
                    html += `<strong class="text-warning">경고:</strong> <small>${warnItems.slice(0, 2).join(', ')}</small>`;
                }
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

