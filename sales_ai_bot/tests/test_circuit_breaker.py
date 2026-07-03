import pytest
import time
from app.core.gigachat_service import CircuitBreaker, CircuitState


class TestCircuitBreaker:
    """Тесты для Circuit Breaker паттерна."""
    
    def test_initial_state_is_closed(self):
        """Circuit Breaker должен начинаться в состоянии CLOSED."""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=10)
        assert cb.state == CircuitState.CLOSED
        assert cb.can_execute() is True
    
    def test_opens_after_threshold_failures(self):
        """Circuit Breaker должен открываться после N ошибок."""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=10)
        
        # Симулируем 3 ошибки
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED  # Еще не открыт
        
        cb.record_failure()
        assert cb.state == CircuitState.OPEN  # Теперь открыт
        assert cb.can_execute() is False
    
    def test_success_resets_failure_count(self):
        """Успешный вызов должен сбрасывать счетчик ошибок."""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=10)
        
        cb.record_failure()
        cb.record_failure()
        cb.record_success()  # Сбрасывает счетчик
        
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED  # Не открылся
    
    def test_transitions_to_half_open_after_timeout(self):
        """Circuit Breaker должен переходить в HALF_OPEN после таймаута."""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
        
        # Открываем circuit breaker
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        
        # Ждем таймаут
        time.sleep(1.1)
        
        # Проверяем переход
        assert cb.state == CircuitState.HALF_OPEN
        assert cb.can_execute() is True
    
    def test_closes_after_success_in_half_open(self):
        """Circuit Breaker должен закрываться после успешных вызовов в HALF_OPEN."""
        cb = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=1,
            success_threshold=2
        )
        
        # Открываем
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        
        # Ждем таймаут
        time.sleep(1.1)
        assert cb.state == CircuitState.HALF_OPEN
        
        # Два успешных вызова
        cb.record_success()
        assert cb.state == CircuitState.HALF_OPEN  # Еще не закрылся
        
        cb.record_success()
        assert cb.state == CircuitState.CLOSED  # Теперь закрыт
    
    def test_reopens_on_failure_in_half_open(self):
        """Circuit Breaker должен снова открываться при ошибке в HALF_OPEN."""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
        
        # Открываем
        cb.record_failure()
        cb.record_failure()
        
        # Ждем таймаут
        time.sleep(1.1)
        assert cb.state == CircuitState.HALF_OPEN
        
        # Ошибка в HALF_OPEN
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        