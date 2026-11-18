#!/usr/bin/env python3

import argparse
import collections
import json
import re
import subprocess
import sys
from pathlib import Path

DESCRIPTION = """PR（GitLabではMR）のレビューに必要な事実を集め、Markdownで標準出力へ出す。

GitHubは gh で本文、CI、既存のレビューまで取得する。
GitLabはMRのコードを git fetch し、手元の差分から分かる事実だけを出す。
リモートは読むだけである。手元で変えるのは、作業ディレクトリの作成と、git fetch による取得（FETCH_HEAD とリモート追跡ブランチの更新を含む）だけである。"""

SPLIT_FILES = 30
SPLIT_LINES = 1500

PR_FIELDS = (
    "number,title,url,state,isDraft,author,baseRefName,headRefName,headRefOid,baseRefOid,"
    "mergeable,mergeStateStatus,additions,deletions,changedFiles,commits,body,files,"
    "closingIssuesReferences,statusCheckRollup,reviews,comments,mergedAt,labels"
)

MIGRATION_PATH_SIGNALS = [
    ("DBスキーマ・データ移行", r"(^|/)(prisma|migrations?|dataconnect|alembic|db/migrate|drizzle|liquibase)/|(^|/)schema\.(prisma|rb)$|\.sql$|(^|/)(migrate|backfill)[-_A-Z.]"),
    ("APIスキーマ", r"\.(graphql|gql|proto)$|(^|/)(openapi|swagger)[^/]*\.(ya?ml|json)$"),
    ("データストアのルール・インデックス", r"firestore\.rules$|firestore\.indexes\.json$|storage\.rules$|database\.rules\.json$"),
    ("環境変数・実行設定", r"(^|/)\.env(\.[^/]*)?$|(^|/)(Dockerfile|Containerfile)[^/]*$|\.Dockerfile$|(^|/)(docker-)?compose[^/]*\.ya?ml$|(^|/)apphosting[^/]*\.ya?ml$|(^|/)(k8s|kubernetes|helm|charts)/|(^|/)(firebase\.json|vercel\.json|wrangler\.toml|serverless\.ya?ml)$"),
    ("CI・デプロイ手順", r"^\.github/(workflows|actions)/|(^|/)\.gitlab-ci\.yml$|^\.gitlab/ci/|^\.circleci/|(^|/)Jenkinsfile$|(^|/)azure-pipelines[^/]*\.ya?ml$|(^|/)buildspec[^/]*\.ya?ml$|(^|/)cloudbuild[^/]*\.ya?ml$"),
    ("インフラ（Terraform）", r"\.tf(\.json)?$|\.tfvars(\.json)?$|(^|/)\.terraform\.lock\.hcl$|(^|/)terragrunt\.hcl$"),
    ("依存パッケージ", r"(^|/)(package\.json|pnpm-lock\.yaml|pnpm-workspace\.yaml|package-lock\.json|npm-shrinkwrap\.json|yarn\.lock|bun\.lockb?)$|(^|/)requirements[^/]*(\.txt|/[^/]+\.txt)$|(^|/)(pyproject\.toml|poetry\.lock|uv\.lock|Pipfile(\.lock)?|go\.(mod|sum)|Gemfile(\.lock)?|Cargo\.(toml|lock)|pom\.xml|build\.gradle(\.kts)?|composer\.(json|lock)|pubspec\.(yaml|lock))$|(^|/)vendor/"),
]

ADDED_LINE_SIGNALS = [
    ("環境変数の参照", r"process\.env\.([A-Za-z_][A-Za-z0-9_]+)"),
    ("環境変数の参照", r"process\.env\[[\"']([A-Za-z_][A-Za-z0-9_]+)[\"']\]"),
    ("環境変数の参照", r"import\.meta\.env\.([A-Z][A-Z0-9_]+)"),
    ("環境変数の参照", r"(?:os\.environ(?:\.get\(|\[)|os\.getenv\(|os\.Getenv\(|ENV\[|System\.getenv\(|Deno\.env\.get\()[\"']([A-Za-z_][A-Za-z0-9_]+)[\"']"),
    ("Secret・パラメーターの参照", r"define(?:Secret|String|Int|Boolean)\([\"']([A-Za-z0-9_]+)[\"']"),
    ("IAMロール（Google Cloud）", r"(?<![\w/.])(roles/[a-z][A-Za-z0-9]*\.[A-Za-z0-9.]+)"),
    ("IAMのアクション（AWS）", r"(?:[\"']|-\s|:\s)((?:lambda|s3|dynamodb|ssm|secretsmanager|kms|sqs|sns|sts|ec2|ecs|ecr|iam|rds|logs|events|bedrock|execute-api):[A-Z*][A-Za-z*]*)(?=[\"'\s,]|$)"),
    ("GitHub Actionsの変数", r"(?<![\w.])((?:vars|secrets)\.[A-Za-z][A-Za-z0-9_]+)"),
]

TEST_FILE = re.compile(
    r"(^|/)(__tests__|__snapshots__|tests?|e2e|cypress|playwright)/"
    r"|(^|/)spec/.*\.(rb|[jt]sx?)$"
    r"|[._-](test|spec)\.([jt]sx?|mjs|cjs|py|rb|go|dart)$"
    r"|\.cy\.[jt]sx?$"
    r"|(^|/)test_[^/]+\.py$"
    r"|_test\.(go|py|rb|dart)$"
    r"|Tests?\.(java|kt|cs|swift|php)$"
)
NON_SOURCE = re.compile(
    r"\.(mdx?|txt|rst|lock|lockb|json|ya?ml|toml|csv|svg|png|jpe?g|gif|webp|ico|snap)$|(^|/)(LICENSE|\.gitignore|go\.sum)$",
    re.IGNORECASE,
)

FAILED_CHECK_STATES = ("FAILURE", "ERROR", "TIMED_OUT", "CANCELLED", "STARTUP_FAILURE", "ACTION_REQUIRED")
GITHUB_FILES_PER_VIEW = 100
AREA_DEPTH = 4


def run_command(command, cwd=None):
    result = subprocess.run(command, capture_output=True, text=True, cwd=cwd)

    if result.returncode != 0:
        return False, result.stderr.strip()

    return True, result.stdout


def run_gh(*args):
    return run_command(["gh", *args])


def run_git(checkout, *args):
    return run_command(["git", "-C", str(checkout), *args])


def exit_unless_ok(result, message):
    ok, output = result

    if not ok:
        sys.exit(f"{message}: {output}")

    return output.strip()


def find_workspace_root():
    ok, toplevel = run_command(["git", "rev-parse", "--show-toplevel"])

    if ok:
        return Path(toplevel.strip())

    return Path.cwd()


def parse_remote_url(url):
    url = url.strip()
    scp_like = re.match(r"^[^@/]+@([^:/]+):(.+?)(\.git)?/?$", url)

    if scp_like:
        return scp_like.group(1), scp_like.group(2)

    with_scheme = re.match(r"^[a-z+]+://(?:[^@/]+@)?([^:/]+)(?::\d+)?/(.+?)(\.git)?/?$", url)

    if with_scheme:
        return with_scheme.group(1), with_scheme.group(2)

    return None


def read_origin(checkout):
    ok, url = run_git(checkout, "remote", "get-url", "origin")

    if not ok:
        return None

    return parse_remote_url(url)


def is_repository_root(directory):
    ok, toplevel = run_git(directory, "rev-parse", "--show-toplevel")
    return ok and Path(toplevel.strip()).resolve() == directory.resolve()


def read_own_origin(directory):
    if not directory.is_dir() or not is_repository_root(directory):
        return None

    return read_origin(directory)


def is_same_project(origin, host, project_path):
    if origin is None:
        return False

    origin_host, origin_path = origin
    host_without_port = host.split(":")[0]
    return (origin_host.lower(), origin_path.lower()) == (host_without_port.lower(), project_path.lower())


def find_checkout(workspace, host, project_path, repo_argument=None):
    repo_name = project_path.rsplit("/", 1)[-1]
    candidates = [workspace, workspace / "repo" / repo_name]

    if repo_argument:
        candidates = [workspace / "repo" / repo_argument, Path(repo_argument), *candidates]

    for candidate in candidates:
        if is_same_project(read_own_origin(candidate), host, project_path):
            return candidate

    return None


def forge_of(host, forced_forge):
    if forced_forge:
        return forced_forge

    return "github" if "github" in host.lower() else "gitlab"


def resolve_numbered_target(workspace, number, repo_argument, forced_forge):
    if repo_argument is None:
        origin = read_origin(workspace)

        if origin is None:
            sys.exit("番号だけでは対象のリポジトリが分かりません。URLか --repo を指定してください")

        host, project_path = origin
        return forge_of(host, forced_forge), host, project_path, number, workspace

    for candidate in (workspace / "repo" / repo_argument, Path(repo_argument)):
        origin = read_own_origin(candidate)

        if origin:
            host, project_path = origin
            return forge_of(host, forced_forge), host, project_path, number, candidate

    looks_like_owner_and_name = re.fullmatch(r"[\w.-]+/[\w.-]+", repo_argument) and not repo_argument.startswith(".")

    if not looks_like_owner_and_name or forced_forge == "gitlab":
        sys.exit(f"--repo はチェックアウトのパス、repo/ 配下のディレクトリ名、owner/name のいずれかで指定してください: {repo_argument}")

    host = "github.com"
    return "github", host, repo_argument, number, find_checkout(workspace, host, repo_argument)


def resolve_target(workspace, target, repo_argument, forced_forge):
    merge_request = re.search(r"https?://([^/]+)/(.+?)/-/merge_requests/(\d+)", target)

    if merge_request:
        host, project_path, number = merge_request.group(1), merge_request.group(2), int(merge_request.group(3))
        return "gitlab", host, project_path, number, find_checkout(workspace, host, project_path, repo_argument)

    pull_request = re.search(r"https?://([^/]+)/([^/]+/[^/]+)/pull/(\d+)", target)

    if pull_request:
        host, project_path, number = pull_request.group(1), pull_request.group(2), int(pull_request.group(3))
        return "github", host, project_path, number, find_checkout(workspace, host, project_path, repo_argument)

    number = target.lstrip("#!")

    if not number.isdigit():
        sys.exit(f"番号かPRやMRのURLを指定してください: {target}")

    return resolve_numbered_target(workspace, int(number), repo_argument, forced_forge)


def area_of(path):
    directories = path.split("/")[:-1]
    return "/".join(directories[:AREA_DEPTH]) or "(ルート)"


def summarize_checks(rollup):
    counts = collections.Counter()
    failed = []

    for check in rollup or []:
        state = check.get("conclusion") or check.get("state") or check.get("status") or "UNKNOWN"
        counts[state] += 1

        if state in FAILED_CHECK_STATES:
            failed.append(check.get("name") or check.get("context") or "?")

    return counts, failed


def scan_added_lines(diff):
    found = collections.defaultdict(set)

    for line in diff.splitlines():
        is_added_line = line.startswith("+") and not line.startswith("+++ ")

        if not is_added_line:
            continue

        for label, pattern in ADDED_LINE_SIGNALS:
            for value in re.findall(pattern, line):
                found[label].add(value)

    return found


def display_path(path, workspace):
    try:
        return str(path.relative_to(workspace))
    except ValueError:
        return str(path)


def print_header(facts, workspace, out_dir, checkout, repo_name, number, kind):
    workdir = out_dir / f"{repo_name}-{kind}-{number}"
    has_previous_review = (workdir / "review.md").exists()
    workdir.mkdir(parents=True, exist_ok=True)

    changed_lines = facts["additions"] + facts["deletions"]
    file_count = facts.get("file_count", len(facts["files"]))
    should_split = file_count >= SPLIT_FILES or changed_lines >= SPLIT_LINES

    print(facts["heading"] + "\n")

    for line in facts["summary"]:
        print(f"- {line}")

    print(f"- 規模: {file_count}ファイル、+{facts['additions']}/-{facts['deletions']}行、コミット{facts['commits']}件")
    print(f"- 作業ディレクトリ: `{display_path(workdir, workspace)}`（{'review.md あり。再レビュー' if has_previous_review else 'review.md なし。初回のレビュー'}）")
    print(f"- ローカルのチェックアウト: {f'`{display_path(checkout, workspace)}`' if checkout else 'なし。一時ディレクトリへcloneする'}")
    print(f"- 進め方の推奨: {'複数のレビューエージェントに分ける' if should_split else '1人で読む'}"
          f"（基準: {SPLIT_FILES}ファイル以上または{SPLIT_LINES}行以上）")


def print_github_sections(pull_request):
    issues = pull_request.get("closingIssuesReferences") or []
    print("\n## 関連Issue\n")

    if issues:
        for issue in issues:
            print(f"- #{issue['number']} {issue.get('title', '')} {issue.get('url', '')}")
    else:
        print("- GitHub上の紐付けなし。PR本文の `#番号` と外部リンクを確認する")

    counts, failed = summarize_checks(pull_request["statusCheckRollup"])
    print("\n## CI\n")
    print("- " + ("、".join(f"{state}: {count}" for state, count in sorted(counts.items())) or "チェックなし"))

    for name in failed:
        print(f"- 失敗: {name}")

    print(f"\n## 既存のレビュー\n\n- レビュー{len(pull_request['reviews'])}件、会話コメント{len(pull_request['comments'])}件")

    for review in pull_request["reviews"]:
        author = (review.get("author") or {}).get("login", "?")
        print(f"- {author}: {review['state']}")


def print_diff_sections(facts):
    files = facts["files"]
    paths = [item["path"] for item in files]

    print("\n## 領域の候補\n")

    if facts.get("file_list_note"):
        print(f"- 注意: {facts['file_list_note']}")

    changed_lines_by_area = collections.Counter()

    for item in files:
        changed_lines_by_area[area_of(item["path"])] += item["additions"] + item["deletions"]

    for area, count in changed_lines_by_area.most_common(15):
        print(f"- `{area}`: {count}行")

    print("\n## マイグレーションの信号\n")
    any_signal = False

    for label, pattern in MIGRATION_PATH_SIGNALS:
        hits = [path for path in paths if re.search(pattern, path)]

        if hits:
            any_signal = True
            shown = "、".join(f"`{path}`" for path in hits[:8])
            print(f"- {label}（{len(hits)}件）: {shown}" + (" ほか" if len(hits) > 8 else ""))

    diff_ok, diff = facts["diff"]

    if diff_ok:
        for label, values in sorted(scan_added_lines(diff).items()):
            any_signal = True
            print(f"- {label}（追加行）: " + "、".join(f"`{value}`" for value in sorted(values)[:15]))
    else:
        print(f"- 差分を取得できず、追加行は未確認: {diff[:200]}")

    if not any_signal:
        print("- 信号なし。信号がないことは不要の根拠にならないので、差分を読んで判断する")

    tests = [path for path in paths if TEST_FILE.search(path)]
    source = [path for path in paths if not TEST_FILE.search(path) and not NON_SOURCE.search(path)]
    print("\n## テストの変更\n")
    print(f"- テスト{len(tests)}ファイル、それ以外のコード{len(source)}ファイル")

    for path in tests[:20]:
        print(f"- `{path}`")


def list_all_changed_files(host, project_path, number):
    row_of_file = ".[] | [.filename, .additions, .deletions] | @tsv"
    ok, output = run_gh("api", "--hostname", host, "--paginate", f"repos/{project_path}/pulls/{number}/files", "--jq", row_of_file)

    if not ok:
        return None

    files = []

    for line in output.splitlines():
        path, additions, deletions = line.split("\t")
        files.append({"path": path, "additions": int(additions), "deletions": int(deletions)})

    return files


def collect_github_pull_request(workspace, out_dir, host, project_path, number, checkout):
    full_name = project_path if host == "github.com" else f"{host}/{project_path}"
    ok, output = run_gh("pr", "view", str(number), "-R", full_name, "--json", PR_FIELDS)

    if not ok:
        sys.exit(f"PRを取得できません（{full_name}#{number}）: {output}")

    pull_request = json.loads(output)
    merged = f"（マージ: {pull_request['mergedAt']}）" if pull_request["mergedAt"] else ""
    draft = "、ドラフト" if pull_request["isDraft"] else ""
    author = (pull_request.get("author") or {}).get("login", "?")
    files = pull_request["files"]
    file_list_note = None

    if pull_request["changedFiles"] > len(files):
        all_files = list_all_changed_files(host, project_path, number)

        if all_files is None:
            file_list_note = (f"ファイルの一覧は先頭{len(files)}件だけを取得できた（全{pull_request['changedFiles']}件）。"
                              "領域の候補、パスの信号、テストの変更は一部だけの集計である")
        else:
            files = all_files

    facts = {
        "heading": f"# {full_name} #{number}: {pull_request['title']}",
        "summary": [
            f"URL: {pull_request['url']}",
            f"状態: {pull_request['state']}{merged}{draft}",
            f"作成者: {author}",
            f"base: `{pull_request['baseRefName']}` (`{pull_request['baseRefOid']}`)",
            f"head: `{pull_request['headRefName']}` (`{pull_request['headRefOid']}`)",
            f"マージ可否: {pull_request['mergeable']} / {pull_request['mergeStateStatus']}",
        ],
        "files": files,
        "file_count": pull_request["changedFiles"],
        "file_list_note": file_list_note,
        "additions": pull_request["additions"],
        "deletions": pull_request["deletions"],
        "commits": len(pull_request["commits"]),
        "diff": run_gh("pr", "diff", str(number), "-R", full_name),
    }

    print_header(facts, workspace, out_dir, checkout, project_path.rsplit("/", 1)[-1], number, "pr")
    print_github_sections(pull_request)
    print_diff_sections(facts)
    print("\n## PR本文\n")
    print(pull_request["body"] or "（本文なし）")


def detect_default_branch(checkout):
    ok, ref = run_git(checkout, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")

    if ok:
        return ref.strip().removeprefix("origin/")

    return "main"


def collect_gitlab_merge_request(workspace, out_dir, host, project_path, number, checkout, target_branch, base_sha):
    if checkout is None:
        sys.exit(f"GitLabのMRはローカルのチェックアウトから読みます。{project_path} をcloneし、その中で実行するか --repo にパスを渡してください")

    target_branch = target_branch or detect_default_branch(checkout)

    # refs/merge-requests/{番号}/head はGitLabが作る読み取り専用の参照。マージやクローズの後しばらくすると消える。
    exit_unless_ok(run_git(checkout, "fetch", "--quiet", "origin", f"refs/merge-requests/{number}/head"),
                   f"MRを取得できません（{project_path}!{number}）。マージやクローズから時間がたったMRは参照が消えている。"
                   "その場合はソースブランチかマージコミットから読む")
    head = exit_unless_ok(run_git(checkout, "rev-parse", "FETCH_HEAD"), "headを解決できません")
    base = base_sha

    if base is None:
        exit_unless_ok(run_git(checkout, "fetch", "--quiet", "origin", target_branch),
                       f"マージ先の {target_branch} を取得できません。--target-branch を確かめてください")
        base = exit_unless_ok(run_git(checkout, "merge-base", head, "FETCH_HEAD"),
                              "マージベースを求められません。浅いcloneなら git fetch --unshallow を実行してください")

    if base == head:
        sys.exit(f"headが {target_branch} に含まれるので差分を求められません（マージ済みのMR）。"
                 "MRの最も古いコミットを調べ、その親を --base に渡してください")

    files = []
    numstat = exit_unless_ok(run_git(checkout, "-c", "core.quotePath=false", "diff", "--numstat", "--no-renames", base, head), "差分を取得できません")

    for line in numstat.splitlines():
        additions, deletions, path = line.split("\t", 2)
        is_binary = additions == "-"
        files.append({
            "path": path,
            "additions": 0 if is_binary else int(additions),
            "deletions": 0 if is_binary else int(deletions),
        })

    base_origin = "（--base で指定）" if base_sha else f"（`{target_branch}` とのマージベース）"

    facts = {
        "heading": f"# {project_path} !{number}",
        "summary": [
            f"URL: https://{host}/{project_path}/-/merge_requests/{number}",
            f"base: `{base}`{base_origin}",
            f"head: `{head}`",
        ],
        "files": files,
        "additions": sum(item["additions"] for item in files),
        "deletions": sum(item["deletions"] for item in files),
        "commits": int(exit_unless_ok(run_git(checkout, "rev-list", "--count", f"{base}..{head}"), "コミットを数えられません")),
        "diff": run_git(checkout, "diff", "--no-renames", base, head),
    }

    print_header(facts, workspace, out_dir, checkout, project_path.rsplit("/", 1)[-1], number, "mr")
    print_diff_sections(facts)
    print("\n## 別に取得するもの\n")
    print("- 本文、状態、パイプライン、コメント、承認はこのスクリプトでは取得しない。SKILL.md の手順1に従う")
    print("- 規模は手元の差分から求めた。積み上げたMRがスカッシュでマージされた後は、親のMRの差分が混ざることがある。"
          "GitLabが示す規模と食い違うときは、コミットの一覧で範囲を確かめる")


def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("target", help="PRやMRの番号、またはURL")
    parser.add_argument("--repo", help="番号だけを渡すときの対象。チェックアウトのパス、repo/ 配下のディレクトリ名、GitHubの owner/name のいずれか。省略時は現在のリポジトリ")
    parser.add_argument("--forge", choices=["github", "gitlab"], help="originのホスト名から判断できないときに指定する")
    parser.add_argument("--out-dir", default="tasks/reviews", help="作業ディレクトリを作る場所。ワークスペースのルートからの相対パス")
    parser.add_argument("--target-branch", help="GitLabのMRのマージ先。省略時は origin のデフォルトブランチ")
    parser.add_argument("--base", help="GitLabのMRの差分の起点。マージ済みでマージベースを求められないときに指定する")
    args = parser.parse_args()

    workspace = find_workspace_root()
    out_dir = workspace / args.out_dir
    forge, host, project_path, number, checkout = resolve_target(workspace, args.target, args.repo, args.forge)

    if forge == "gitlab":
        collect_gitlab_merge_request(workspace, out_dir, host, project_path, number, checkout, args.target_branch, args.base)
    else:
        collect_github_pull_request(workspace, out_dir, host, project_path, number, checkout)


if __name__ == "__main__":
    main()
