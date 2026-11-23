# Eight Sleep connector rules (read-only by default)

- Default to the six read-only Eight Sleep tools: `get_sleep_days`, `get_sleep_sessions`, `get_sleep_session`, `get_device_status`, `get_temperature_settings`, and `list_alarms`.
- Never call device-mutation tools (`create_alarm`, `update_alarm`, `delete_alarm`, `set_pod_power`, `set_temperature`, `update_temperature_schedule`) unless the user explicitly asks to change a Pod setting or alarm and confirms the exact change first.
- Report sleep stages, scores, heart rate, heart rate variability, respiratory rate, and snoring strictly as measurements from the Eight Sleep account and Pod, never as medical advice or diagnosis.
- Never print, log, or commit Open Authorization (OAuth) tokens, authorization codes, or callback Uniform Resource Locators (URLs).
