#!/usr/bin/env python3

import os
import sys
import shutil
from PyPDF2 import PdfFileReader
from plumbum import local, FG, cli
from plumbum.commands.modifiers import ExecutionModifier, Future


cfg = {
    'USERNAME': '',
    'PASSWORD': '',
    'PUBLIC': False,
    'THRESHOLD': 100,
    'REPO': '',
    'ASKPASS': '/tmp/askpass',
    'FORCE': False,
}

SSH_ASKPASS = '''#!/bin/bash
case "$1" in
  *sername*)
    echo "{USERNAME}"
    ;;
  *assword*)
    echo "{PASSWORD}"
    ;;
esac'''

HUB_CONFIG_CACHE = '~/.config/hub'


def check_req() -> None:
    print('[ Checking for requirements ... ]')

    reqs = ('ebook-convert', 'unar', 'git', 'hub')
    installs = []

    for cmd in reqs:
        try:
            local[cmd]
        except Exception:
            installs.append(cmd)

    if installs:
        print('please install ' + ' '.join(installs))
        sys.exit(1)


def pdf_is_scanned(pdf_path):
    with open(pdf_path, 'rb') as f:
        pdf = PdfFileReader(f)
        pages_num = pdf.getNumPages()
        text_num = 0
        for page in pdf.pages:
            if len(page.extractText()) > cfg['THRESHOLD']:
                text_num += 1
        rate = text_num / pages_num
        print(
            f'Total pages: {pages_num}\nText pages: {text_num}\nRate: {rate}')
        return rate < cfg['RATE']


def doc2html(input, output):
    from plumbum.cmd import unar, rm
    ebook_convert = local['ebook-convert']

    outfile = f'{output}.htmlz'
    ebook_convert[input, outfile] & FG
    unar['-f', outfile] & FG
    rm[outfile] & FG


def gen_sshaskpass(path):
    from plumbum.cmd import chmod
    with open(path, 'w') as f:
        content = SSH_ASKPASS.format(
            USERNAME=cfg['USERNAME'], PASSWORD=cfg['PASSWORD'])
        f.write(content)

    chmod['+x', path] & FG


def publish_html(repo):
    from datetime import datetime
    from plumbum.cmd import git, hub, printf, rm

    _start_time = datetime.now().timestamp()

    user = cfg['USERNAME']
    password = cfg['PASSWORD']

    cwd = os.path.abspath(os.curdir)
    os.chdir(repo)
    git['init'] & FG
    git['config', 'user.name', user] & FG
    git['config', 'user.email', '<>'] & FG
    git['checkout', '-b', 'gh-pages'] & FG
    git['add', '-A'] & FG
    git['commit', '-m', 'Initial commit'] & FG

    # hub would read username and password from stdin
    # inputer = printf[f'{user}\n{password}\n']
    # if cfg['PUBLIC']:
    #     (inputer | hub['create']) & FG
    # else:
    #     (inputer | hub['create', '-p']) & FG

    # auth by username and password
    # export GIT_ASKPASS=/path/to/askpass
    # the askpass program would return username or password based
    # on prompt message.
    _askpass = cfg['ASKPASS']
    gen_sshaskpass(_askpass)

    # HUB_PROTOCOL=https make hub to add origin with https protocol
    with local.env(GITHUB_USER=user, GITHUB_PASSWORD=password, HUB_PROTOCOL='https', GIT_ASKPASS=_askpass):
        if cfg['PUBLIC']:
            hub['create'] & FG
        else:
            hub['create', '-p'] & FG
        git['push', 'origin', 'gh-pages'] & FG

    # call command and it's return value is output.
    # remote_url = git['remote', 'get-url', 'origin']()

    rm['-f', _askpass] & FG

    # delete cached hub token
    if os.path.isfile(HUB_CONFIG_CACHE):
        # If the HUB_CONFIG_CACHE file is modified after starting of this function,
        # just delete it for security consideration.
        _modify_time = os.path.getmtime(HUB_CONFIG_CACHE)
        if _modify_time > _start_time:
            rm['-f', HUB_CONFIG_CACHE] & FG

    print(
        f'Document is published at: https://{user.lower()}.github.io/{repo}/')
    os.chdir(cwd)


def _main(doc_path, output):
    import getpass

    check_req()

    cfg['PASSWORD'] = getpass.getpass('github password:')

    ext = os.path.splitext(doc_path)[-1]
    if ext == '.pdf':
        if cfg['FORCE']:
            print('Force to convert PDF.')
        elif pdf_is_scanned(doc_path):
            print('PDF is scanned, cannot be converted.')
            sys.exit(1)

    doc2html(doc_path, output)
    publish_html(output)
    shutil.rmtree(output, ignore_errors=True)


class App(cli.Application):
    """Convert a document to html and deploy the html with github pages.

    doc_path: path of a document, such as xxx-xxx.pdf or /path/to/xxx-xxx.epub
    repo: <username>/<repo> the repository to be deployed on github.
    """

    public = cli.Flag('--public', default=False,
                      help='Deploy to an public repository.')
    threshold = cli.SwitchAttr('--pdf-threshold', argtype=int, default=100,
                               help='Character number threshold. Only works for pdf file. When number of characters in a page is larger than threshold, then the page is thought as a text page.')
    rate = cli.SwitchAttr('--pdf-rate', argtype=float, default=0.6,
                          help="Minimum rate of text pages over total pages. Only works for pdf file. If the actual rate is below this value, the pdf file is thought as a scanned document, which won't be converted.")
    force = cli.Flag('--pdf-force', default=False,
                     help="Force to convert pdf despite whether it's scanned or not.")

    def main(self, doc_path, repo):
        # Split "<username>/<repo>"
        splited = repo.split('/')
        if not (len(splited) == 2 and all(splited)):
            print(f'Invalid repo: {repo}')
            sys.exit(1)

        cfg['USERNAME'], cfg['REPO'] = splited
        cfg['PUBLIC'] = self.public
        cfg['THRESHOLD'] = self.threshold
        cfg['RATE'] = self.rate
        cfg['FORCE'] = self.force

        _main(doc_path, cfg['REPO'])


if __name__ == '__main__':
    App.run()
