/**
 * WebSocket 클라이언트
 */
class WebSocketClient {
    constructor() {
        this.ws = null;
        this.reconnectInterval = 3000;
        this.reconnectTimer = null;
        this.listeners = new Map();
    }
    
    /**
     * WebSocket 연결
     */
    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/api/checks/ws`;
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket 연결됨');
                this.onConnect();
            };
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket 오류:', error);
                this.onError(error);
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket 연결 해제됨');
                this.onDisconnect();
                // 자동 재연결
                this.scheduleReconnect();
            };
        } catch (error) {
            console.error('WebSocket 연결 실패:', error);
            this.scheduleReconnect();
        }
    }
    
    /**
     * 재연결 스케줄
     */
    scheduleReconnect() {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
        }
        
        this.reconnectTimer = setTimeout(() => {
            console.log('WebSocket 재연결 시도...');
            this.connect();
        }, this.reconnectInterval);
    }
    
    /**
     * 연결 성공 시
     */
    onConnect() {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
        this.emit('connect');
    }
    
    /**
     * 연결 해제 시
     */
    onDisconnect() {
        this.emit('disconnect');
    }
    
    /**
     * 오류 발생 시
     */
    onError(error) {
        this.emit('error', error);
    }
    
    /**
     * 메시지 처리
     */
    handleMessage(data) {
        const { type, check_type, progress, message, status, result, error } = data;
        
        switch (type) {
            case 'progress':
                this.emit('progress', {
                    checkType: check_type,
                    progress: progress,
                    message: message,
                    status: status
                });
                break;
            
            case 'result':
                this.emit('result', {
                    checkType: check_type,
                    result: result
                });
                break;
            
            case 'error':
                this.emit('error', {
                    checkType: check_type,
                    error: error
                });
                break;
        }
    }
    
    /**
     * 이벤트 리스너 등록
     */
    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }
    
    /**
     * 이벤트 리스너 제거
     */
    off(event, callback) {
        if (!this.listeners.has(event)) return;
        
        const callbacks = this.listeners.get(event);
        const index = callbacks.indexOf(callback);
        if (index > -1) {
            callbacks.splice(index, 1);
        }
    }
    
    /**
     * 이벤트 발생
     */
    emit(event, data) {
        if (!this.listeners.has(event)) return;
        
        this.listeners.get(event).forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error(`이벤트 리스너 오류 (${event}):`, error);
            }
        });
    }
    
    /**
     * 연결 종료
     */
    disconnect() {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
        
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}

// 전역 인스턴스
const wsClient = new WebSocketClient();

