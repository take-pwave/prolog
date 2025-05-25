# prolog
このプロジェクトでは、以下の2つのテーマを扱います。
- JAVAによるパーサ構築技法（Building parser with Java）の推論エンジンとパーサをpythonに移植する
- Prologの技芸（Art of Prolog）の数式処理とパーサの例題を試す

## JAVAによるパーサ構築技法について

JAVAによるパーサ構築技法は、絶版になっており、Javaのソースは、Githubからダウンロードできます。
- https://github.com/sujitpal/bpwj.git

以下では、Javaソースと見比べながら移植するために、サブモジュールとして追加します。

```bash
% git submodule add https://github.com/sujitpal/bpwj.git
```

私は古書をAmazonから購入しましたが、これから試すJavaからPythonへの移行については、Javaのソースコードがあれば、なんとかトレースできると思います。

### 推論エンジンの移植
これから移植するのは正式な Prologではなく、「JAVAによるパーサ構築技法」の12章から14章で紹介されている推論エンジンLogikusの移植です。

エンジン移植の手順は、以下のノートブックで説明します。
- porting_engine.ipynb

簡易Prolog(Logikus)パーサの移植は、以下に説明しています。
- porting_parser.ipynb




