import matplotlib.pyplot as plt
import pandas as pd
import json

data_folder = 'data'

vllm_file = f'{data_folder}/stress-tests_run_20260311_001025.json'
claude_file = f'{data_folder}/stress-tests_run_20260311_004901.json'
claude_file = f'{data_folder}/tests_run_20260311_023618.json'

with open(vllm_file, 'r') as file:
    data = json.load(file)
df_vllm = pd.json_normalize(data).drop(['node'], axis=1)
df_vllm.columns = [col if 'metrics' not in col else col.removeprefix('metrics.') for col in df_vllm.columns]
df_vllm['mins'] = df_vllm['duration'] / 60.

print(df_vllm)

with open(claude_file, 'r') as file:
    data = json.load(file)
df_claude = pd.json_normalize(data).drop(['node'], axis=1)
df_claude.columns = [col if 'metrics' not in col else col.removeprefix('metrics.') for col in df_claude.columns]
df_claude['mins'] = df_claude['duration'] / 60.
print(df_claude)

fig, (ax1, ax2, ax3) = plt.subplots(nrows=3, sharex=True)
fig.subplots_adjust(hspace=0)
ax1.plot(df_vllm['concurrency'], df_vllm['user_latency_p50'], color='cyan', marker='o', ls='-')
ax1.plot(df_claude['concurrency'], df_claude['user_latency_p50'], color='green', marker='o', ls='-')
ax1.set_ylabel('Latency in seconds per user')
ax1.set_xlabel('')
ax1.set_xticks([])
ax1.set_xticklabels([])

ax2.plot(df_vllm['concurrency'], df_vllm['n_requests'] / df_vllm['mins'], color='cyan', marker='o', ls='-')
ax2.plot(df_claude['concurrency'], df_claude['n_requests'] / df_claude['mins'], color='green', marker='o', ls='-')
ax2.set_ylabel('Requests per minute (RPM)')
ax2.set_xlabel('')
ax2.set_xticks([])
ax2.set_xticklabels([])

ax3.plot(df_vllm['concurrency'], df_vllm['throughput'], color='cyan', marker='o', ls='-')
ax3.plot(df_claude['concurrency'], df_claude['throughput'], color='green', marker='o', ls='-')
ax3.set_ylabel('Total tokens per second (System TPS)')
ax3.set_xlabel('Concurrent users')
ax3.set_xticks(df_vllm['concurrency'])
ax3.set_xticklabels(df_vllm['concurrency'])

c_req_saas = (1500 * 3 + 500 * 15) / 1e6
instance_hourly_cost = 2.
instance_hourly_capacity = 7200
requests_per_hour = [10, 50, 100, 500, 1000, 1500]
requests_per_day = [r * 8 for r in requests_per_hour]
print(requests_per_day)
c_req_saas_day = [r * c_req_saas for r in requests_per_day]
c_req_slm_day = [instance_hourly_cost * 8 * (r // instance_hourly_capacity + 1) for r in requests_per_hour]
print(c_req_slm_day)

plt.show()
plt.plot(requests_per_hour, c_req_saas_day)
plt.plot(requests_per_hour, c_req_slm_day)
plt.show()