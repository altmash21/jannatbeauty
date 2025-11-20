"""
Centralized logging configuration and utilities.
"""
import logging
from typing import Optional
from functools import wraps


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Logger name (usually __name__).
        
    Returns:
        Configured logger instance.
    """
    return logging.getLogger(name)


def log_view_execution(logger: logging.Logger):
    """
    Decorator to log view execution time and errors.
    
    Args:
        logger: Logger instance to use.
        
    Returns:
        Decorator function.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            import time
            start_time = time.time()
            
            try:
                logger.info(f"View {func.__name__} called by user: {request.user if hasattr(request, 'user') else 'Anonymous'}")
                result = func(request, *args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(f"View {func.__name__} completed in {execution_time:.3f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"View {func.__name__} failed after {execution_time:.3f}s: {str(e)}",
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator


def log_service_call(service_name: str):
    """
    Decorator to log service method calls.
    
    Args:
        service_name: Name of the service.
        
    Returns:
        Decorator function.
    """
    logger = get_logger(f'services.{service_name}')
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                logger.debug(f"Service method {func.__name__} called with args: {args}, kwargs: {kwargs}")
                result = func(*args, **kwargs)
                logger.debug(f"Service method {func.__name__} completed successfully")
                return result
            except Exception as e:
                logger.error(
                    f"Service method {func.__name__} failed: {str(e)}",
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator

