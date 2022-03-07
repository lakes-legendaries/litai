"""Delete old, untagged images on GHCR"""

import json
import os
from os.path import isfile
from subprocess import run


if __name__ == '__main__':

    # get git token
    if 'GIT_TOKEN' in os.environ:
        git_token = os.environ['GIT_TOKEN']
    elif isfile('.dockerkey'):
        git_token = open('.dockerkey').read().strip()
    else:
        raise PermissionError(
            'No access to GHCR. '
            'You must provide a git token, either as a '
            '.dockerkey file, or as the env var GIT_TOKEN.'
        )

    # get current versions
    response = json.loads(run(
        f"""
            curl -u lakes-legendaries:{git_token}
            https://api.github.com/user/packages/container/litai/versions
        """.split(),
        capture_output=True,
        check=True,
        text=True,
    ).stdout)

    # delete untagged versions
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
