from dataclasses import dataclass

@dataclass
class NotificationConfig:
    smtp_host: str = 'smtp.gmail.com'
    smtp_port: int = '587'
    username: str = ''
    password: str = ''
    from_addr: str = ''
    to_addrs: str = ''
    enabled: bool = False
    use_ssl: bool = False
    on_finish: bool = True
    on_error: bool = True
