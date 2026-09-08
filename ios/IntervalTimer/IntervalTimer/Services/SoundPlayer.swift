import AudioToolbox

/// Plays short cues on phase transitions. Uses built-in system sound IDs as
/// a zero-asset placeholder — swap in bundled sound files via
/// `AVAudioPlayer` for guaranteed, reviewable tones before shipping.
struct SoundPlayer {
    private let workStartSound: SystemSoundID = 1113
    private let restStartSound: SystemSoundID = 1114
    private let finishSound: SystemSoundID = 1025

    func playTransition(for newPhase: IntervalPhase) {
        switch newPhase {
        case .work: AudioServicesPlaySystemSound(workStartSound)
        case .rest: AudioServicesPlaySystemSound(restStartSound)
        case .prepare, .finished: break
        }
    }

    func playFinish() {
        AudioServicesPlaySystemSound(finishSound)
    }
}
