# coding=utf-8
import requests.adapters

ADAPTER_WITH_RETRY = requests.adapters.HTTPAdapter(
    max_retries=requests.adapters.Retry(
        total=10,
        status_forcelist=[403, 408, 500, 502],
        connect=0,
    )
)
