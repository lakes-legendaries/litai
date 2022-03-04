"""Make JSON for batch job submission"""

from datetime import datetime
import json
import re


if __name__ == '__main__':
    json.dump(
        {
            'commandLine': re.sub(
                r'\s{2,}',
                ' ',
                r"""
                    /bin/bash -c "
                        git clone https://github.com/lakes-legendaries/litai.git
                        && cd litai
                        && cmd/update-databases
                    "
                """,  # noqa
            ),
            'id': f"litai-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}",
            'userIdentity': {
                'autoUser': {
                    'scope': 'pool',
                    'elevationLevel': 'admin',
                },
            },
        },
        open('batch.json', 'w'),
    )
