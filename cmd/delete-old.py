"""Delete old, untagged images on GHCR"""

import json
from subprocess import run


if __name__ == '__main__':

    # get current versions
    git_token = open('.dockerkey').read().strip()
    response = json.loads(run(
        f"""
            curl -u lakes-legendaries:{git_token}
            https://api.github.com/user/packages/container/litai/versions
        """.split(),
        capture_output=True,
        check=True,
        text=True,
    ).stdout)
    for version in response:
        if not version['metadata']['container']['tags']:
            id = version['id']
            run(
                f"""
                    curl -u lakes-legendaries:{git_token} -X DELETE
                    https://api.github.com/user/packages/container/litai/versions/{id}
                """.split(),
                check=True,
            )
