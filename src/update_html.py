from bs4 import BeautifulSoup


# BootstrapのCSSとJavaScriptのリンク
BOOTSTRAP_LINKS = """
<link rel="stylesheet" href="styles.css">
<link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-pzjw8f+ua7Kw1TIq0v8FqFjcJ6pajs/rfdfs3SO+kD4Ck5BdPtF+to8xM6B5z6W5" crossorigin="anonymous">
<script src="https://code.jquery.com/jquery-3.5.1.slim.min.js" integrity="sha384-DfXdz2htPH0lsSSs5nCTpuj/zy4C+OGpamoFVy38MVBnE+IbbVYUew+OrCXaRkfj" crossorigin="anonymous"></script>
<script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.9.1/dist/umd/popper.min.js" integrity="sha384-eMNCOe7tC1doHpGoJtKh7z7lGz7fuP4F8nfdFvAOA6Gg/z6Y5J6XqqyGXYM2ntX5" crossorigin="anonymous"></script>
<script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js" integrity="sha384-pzjw8f+ua7Kw1TIq0v8FqFjcJ6pajs/rfdfs3SO+kD4Ck5BdPtF+to8xM6B5z6W5" crossorigin="anonymous"></script>
"""

# 固定のナビゲーションバー
NAVBAR = """
<nav class="navbar navbar-expand-lg navbar-light bg-light">
  <div class="container-fluid">
    <a class="navbar-brand" href="#">expected ROE vs. expected PER</a>
  </div>
</nav>
"""

# フッター
FOOTER = """
<footer class="bg-light text-center text-lg-start">
  <div class="text-center p-3" style="background-color: rgba(0, 0, 0, 0.2);">
    © 2023 HiroshimaEasy ltd.
  </div>
</footer>
<script src="script.js"></script>
"""

# all_graphs.htmlから内容を読み込む
with open('web/all_graphs.html', 'r') as file:
    all_graphs_content = file.read()

# BeautifulSoupオブジェクトを作成
soup = BeautifulSoup(all_graphs_content, 'html.parser')

# 特定のdivタグを探索し、idを付与する
div_tag = soup.find('div')
if div_tag:
    div_tag['id'] = 'graph'

# headタグにBootstrapのリンクを追加
head = soup.head
head.insert(1, BeautifulSoup(BOOTSTRAP_LINKS, 'html.parser'))

# bodyタグの最初にナビゲーションバーを追加
body = soup.body
body.insert(0, BeautifulSoup(NAVBAR, 'html.parser'))


# bodyタグの最後にフッターを追加
body.append(BeautifulSoup(FOOTER, 'html.parser'))

# 結果を新しいHTMLファイルに書き出す
with open('docs/index.html', 'w') as file:
    file.write(str(soup))
