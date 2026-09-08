import AVFoundation
import AudioToolbox

/// Plays genuine (but silent) audio through an active `AVAudioSession` while
/// the interval timer is running, so the process is not suspended when the
/// app is backgrounded. This is the standard technique interval/workout
/// timer apps use to keep a `Timer` firing and phase-transition sounds
/// playing while backgrounded; it requires the "Audio, AirPlay, and Picture
/// in Picture" background mode capability plus `UIBackgroundModes: audio`
/// in Info.plist. See the module README for the App Store review note on
/// this pattern.
final class BackgroundAudioKeepAlive {
    private let engine = AVAudioEngine()
    private var isRunning = false

    func start() {
        guard !isRunning else { return }
        configureAudioSession()

        let format = AVAudioFormat(standardFormatWithSampleRate: 44100, channels: 1)!
        let silentSource = AVAudioSourceNode { isSilence, _, _, _ in
            isSilence.pointee = true
            return noErr
        }
        engine.attach(silentSource)
        engine.connect(silentSource, to: engine.mainMixerNode, format: format)
        engine.mainMixerNode.outputVolume = 0

        do {
            try engine.start()
            isRunning = true
        } catch {
            print("BackgroundAudioKeepAlive start failed: \(error)")
        }
    }

    func stop() {
        guard isRunning else { return }
        engine.stop()
        isRunning = false
        try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
    }

    private func configureAudioSession() {
        let session = AVAudioSession.sharedInstance()
        do {
            try session.setCategory(.playback, mode: .default, options: [])
            try session.setActive(true)
        } catch {
            print("AVAudioSession configuration failed: \(error)")
        }
    }
}
