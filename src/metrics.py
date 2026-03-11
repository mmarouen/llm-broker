from pydantic import BaseModel

class UserMetrics(BaseModel):
    output_tokens: int=None
    input_tokens: int=None
    ttft: float=None
    latency: float=None
    tps: float=None

class StageReport(BaseModel):
    n_requests_gross: int=None
    n_requests: int=None
    total_tokens: int=None
    throughput: float=None
    ttft_p50: float=None
    ttft_p95: float=None
    user_latency_p50: float=None
    user_latency_p95: float=None
    output_tokens_p50: int=None
    output_tokens_p95: int=None
    input_tokens_p50: int=None
    input_tokens_p95: int=None
