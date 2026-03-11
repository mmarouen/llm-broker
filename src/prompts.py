LISO_PROMPTS = [
# 1 — Technical documentation summarization
(
"Below is internal documentation about automotive LiDAR calibration procedures. "
"Read the documentation and produce a concise 200-300 word summary highlighting "
"the calibration steps, safety checks, and potential failure points.\n\n"
+ ("LiDAR calibration requires aligning the sensor with the vehicle coordinate "
   "system and verifying timing synchronization between perception modules. "
   "Calibration logs indicate voltage stability, signal noise thresholds, and "
   "point-cloud density measurements. ") * 30
),

# 2 — RAG-style question answering
(
"You are an automotive diagnostics assistant. Using the context below, answer "
"the question at the end in less than 250 words.\n\n"
"Context:\n"
+ ("Vehicle telemetry logs show repeated voltage dips in the ECU power rail. "
   "These events occur during high CPU load scenarios when the perception stack "
   "processes camera and radar frames simultaneously. ") * 40
+ "\n\nQuestion:\nWhat is the most likely cause of the voltage instability and how could it be mitigated?"
),

# 3 — Log analysis
(
"Analyze the following embedded system logs and explain the most likely system "
"failure cause. Provide a short technical explanation and recommend two fixes.\n\n"
+ ("[WARN] ECU_TEMP_SPIKE detected in module ADAS_CTRL. "
   "[INFO] Fan controller adjusting RPM. "
   "[ERROR] Voltage regulator output unstable. "
   "[DEBUG] Sensor fusion latency increased. ") * 35
),

# 4 — Policy / compliance analysis
(
"Read the compliance document below and identify the three most critical safety "
"requirements for ISO 26262 ASIL-D certification. Provide a concise explanation.\n\n"
+ ("ISO 26262 defines functional safety requirements for automotive electronic "
   "systems. The standard specifies hazard analysis procedures, risk "
   "classification, and verification steps across development stages. ") * 40
),

# 5 — Incident report summarization
(
"You are reviewing a vehicle incident report. Summarize the root cause and "
"provide two recommendations for preventing future incidents.\n\n"
+ ("Incident timestamp 14:03:22. Vehicle detected pedestrian crossing but "
   "braking response was delayed by 220 milliseconds due to sensor fusion "
   "queue congestion. The perception module attempted fallback processing "
   "using radar data but object classification confidence dropped. ") * 30
),

]