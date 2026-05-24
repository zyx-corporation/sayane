---
name: Bug report
description: Report incorrect behavior, regression, or security/privacy issue
title: "[Bug]: "
labels: ["type: bug", "needs: triage"]
assignees: []
---

## 概要

何が起きたかを簡潔に書く。

## 再現手順

1. 
2. 
3. 

## 期待される動作

本来どう動くべきかを書く。

## 実際の動作

実際にどう動いたかを書く。

## 影響範囲

- [ ] Core
- [ ] CLI
- [ ] Local Bridge
- [ ] MCP Server
- [ ] Chrome Extension
- [ ] Adapter
- [ ] Evaluator
- [ ] Storage
- [ ] Documentation
- [ ] Security/privacy

## 環境

```text
OS:
Python:
Node:
Browser:
Sayane version / commit:
```

## ログ / 出力

機微情報、token、API key、private keyを含めないこと。

```text
ここにログを貼る
```

## RDE観点

### 保存された要素

修正後も保存すべき仕様・意味・挙動を書く。

### 疑わしい逸脱

この不具合がどのような意味変化、Profile汚染、policy逸脱、誤変換を引き起こし得るかを書く。

### 重大な歪曲の可能性

ユーザーの人格的文脈、values、policy、identityを誤って扱う可能性がある場合は明記する。

## テスト方針

この不具合を再発防止するためのテストを書く。

- [ ] Reproduction test
- [ ] Regression test
- [ ] Contract test
- [ ] Security/privacy test

## Security / Privacy確認

- [ ] secretがログや出力に含まれていない
- [ ] Profile本体が意図せず変更されていない
- [ ] Candidate Updateが承認なしにmergeされていない
- [ ] localhost / MCP / Extension境界に影響がない

## 追加情報

補足があれば書く。
