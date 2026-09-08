import SwiftUI

struct TimerConfigView: View {
    @Binding var config: IntervalTimerConfig
    @ObservedObject var engine: IntervalTimerEngine

    var body: some View {
        Form {
            Section("タイマー名") {
                TextField("インターバルタイマー", text: $config.name)
            }
            Section("時間設定") {
                Stepper("準備: \(config.prepareSeconds)秒", value: $config.prepareSeconds, in: 0...60, step: 5)
                Stepper("運動: \(config.workSeconds)秒", value: $config.workSeconds, in: 5...600, step: 5)
                Stepper("休憩: \(config.restSeconds)秒", value: $config.restSeconds, in: 0...300, step: 5)
                Stepper("セット数: \(config.rounds)", value: $config.rounds, in: 1...50)
            }
            if engine.runState == .finished {
                Section {
                    Label("完了しました", systemImage: "checkmark.circle.fill")
                        .foregroundStyle(.green)
                }
            }
            Section {
                Button {
                    engine.configure(config)
                    engine.start()
                } label: {
                    Label("スタート", systemImage: "play.fill")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
            }
        }
    }
}
