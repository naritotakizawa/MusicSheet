# テスト内容

- MusicPart コンポーネントがパート名を表示すること
- パート名を編集すると `update:part` が発火すること
- 音符を別の音符に変更でき、その結果の `notesInput` が正しいこと
- 音符の長さを8分や16分に変更すると不足分の休符が自動挿入されること
- 音符を休符に変更できること
- 休符を音符に変更できること
- 音符を削除すると小節の長さが埋まるよう休符が追加されること
- 休符をクリックすると音符編集ポップアップが開くこと
- 休符フラグが正しくパースされること
- 小節番号が表示されること
- 小節モデルでノートが管理され、更新時に余分なノートが削除されること
