# IntervalTimer (iOS)

インターバルタイマーアプリ。バックグラウンドで計測・通知を継続し、ロック画面 /
ダイナミックアイランド（Dynamic Island）に現在のフェーズと残り時間を表示する。

このディレクトリは Xcode プロジェクトの `.xcodeproj` を含みません（この開発環境は
Linux コンテナで Xcode を実行できないため、手作業で pbxproj を生成すると壊れる
リスクが高く、意図的に含めていません）。ソースコードのみを用意しているので、
以下の手順で Xcode 上にプロジェクトを組み立ててください。**この環境では
ビルド・実行・実機/シミュレータでの動作確認を行っていません。** Xcode
（macOS, iOS 16.1 以降 SDK、Dynamic Island の完全な検証には iPhone 14 Pro 以降の
実機または Xcode 15+ の対応シミュレータ）で必ず動作確認してください。

## 仕組みの概要

- `IntervalTimerEngine`（`IntervalTimer/Engine/`）: 経過時間ではなく
  `phaseEndDate`（フェーズ終了時刻）という日付を真実の源として管理する状態機械。
  アプリがバックグラウンドでサスペンドされても、フォアグラウンド復帰時に
  `reconcileAfterForeground()` で見逃した遷移を追いつく。
- `BackgroundAudioKeepAlive`（`Services/`）: 無音の `AVAudioEngine` を
  再生し続けることでプロセスのサスペンドを防ぎ、バックグラウンドでも
  `Timer` によるフェーズ遷移とサウンド再生を継続させる、インターバル
  タイマー系アプリで一般的な手法。`UIBackgroundModes: audio` が必要。
- `IntervalNotificationScheduler`（`Services/`）: 全フェーズ遷移分の
  ローカル通知を事前にまとめてスケジュールする保険機構。バックグラウンド
  音声の抑制やプロセス終了があっても、通知は OS 側で保証される。
- `LiveActivityController` + `IntervalTimerWidget`: ActivityKit の
  Live Activity。`Text(timerInterval:countsDown:)` を使うことで、
  アプリ／ウィジェットのコードが動いていなくても OS が自動で
  カウントダウン表示を更新する。ダイナミックアイランドの compact /
  expanded / minimal 表示とロック画面表示を実装。

## Xcode プロジェクトの組み立て手順

1. Xcode で **File > New > Project > iOS > App** を選択し、
   Interface: SwiftUI, Language: Swift でプロジェクト名 `IntervalTimer`
   を作成する（保存先はこの `ios/IntervalTimer/` でよい）。
   **Minimum Deployments は iOS 16.2 以上**にすること
   （`Activity.request(attributes:content:)` の `ActivityContent` API が
   iOS 16.2 以降のため）。
2. テンプレートが生成した `ContentView.swift` / `<AppName>App.swift`
   を削除し、代わりにこのリポジトリの以下のファイルを `IntervalTimer`
   ターゲットに追加する（グループ構成もそのまま踏襲）:
   - `IntervalTimer/IntervalTimerApp.swift`
   - `IntervalTimer/Models/IntervalTimerConfig.swift`
   - `IntervalTimer/Engine/IntervalTimerEngine.swift`
   - `IntervalTimer/Services/*.swift`
   - `IntervalTimer/Views/*.swift`
3. **File > New > Target > Widget Extension** を選択し、名前を
   `IntervalTimerWidget` にする。**"Include Live Activity" に必ず
   チェックを入れる。** テンプレートが生成したプレースホルダーの
   Swift ファイルは削除し、代わりに `IntervalTimerWidget/*.swift`
   を `IntervalTimerWidget` ターゲットに追加する。
4. `Shared/IntervalPhase.swift` と `Shared/IntervalActivityAttributes.swift`
   の2ファイルを、**`IntervalTimer` と `IntervalTimerWidget` の両方の
   ターゲットメンバーシップ**に追加する（Xcode の File Inspector →
   Target Membership で両方にチェック）。Live Activity の状態を
   アプリとウィジェット拡張が共有する型のため。
5. `IntervalTimer` ターゲット → **Signing & Capabilities** → `+ Capability`
   → **Background Modes** を追加し、**"Audio, AirPlay, and Picture in
   Picture"** にチェックを入れる。
6. `IntervalTimer` ターゲットの Info（Info.plist）に以下を追加する:
   - `NSSupportsLiveActivities` (Boolean) = `YES`
   - `UIBackgroundModes` (Array) に `audio` を追加
     （手順5でBackground Modesにチェックすると自動生成される場合あり。
     未生成なら手動で追加）
7. 実行してローカル通知の許可ダイアログが出たら許可する
   （`ContentView` の `.task` で起動時に要求している）。
8. 実機（iPhone 14 Pro 以降）またはダイナミックアイランド対応の
   Xcode シミュレータでビルド・実行し、タイマー開始 → ホーム画面に
   戻る/ロック → ダイナミックアイランド / ロック画面にフェーズと
   残り時間が表示されること、フェーズが切り替わること、一時停止・
   スキップ・停止操作が反映されることを確認する。

## 既知の注意点・今後の調整ポイント

- `SoundPlayer` はビルトインのシステムサウンド ID
  （非公式・未ドキュメント）をプレースホルダーとして使用している。
  本番でのサウンドを確定させたい場合は、実際の音声ファイルを
  バンドルして `AVAudioPlayer` で再生するよう差し替えること。
- 無音バックグラウンド再生でプロセスを維持する手法は、フィットネス /
  タイマー系アプリで広く使われている一般的なパターンだが、App Store
  審査（ガイドライン 2.5.4: バックグラウンドモードの目的外使用）で
  説明を求められる可能性がある。本アプリでは「バックグラウンドでの
  インターバル通知継続」という実際の用途に紐づく音声セッションであり、
  正当な利用であることを審査コメント欄などで明記できるようにしておくこと。
- Dynamic Island 自体は iPhone 14 Pro / Pro Max 以降のハードウェアでのみ
  実機表示される。それ以外の端末では Live Activity はロック画面と
  通知センターのみに表示される（アプリ機能としては同じロジックで動作）。
