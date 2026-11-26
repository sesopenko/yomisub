"""Behavior checks shared by fake and production adapter tests."""

def check_binding(case, provider, stage, physical_id):
    devices = provider.devices()
    case.assertTrue(any(item.physical_id == physical_id and stage in item.stages for item in devices))
    target = provider.bind(stage, physical_id)
    case.assertEqual((target.provider, target.physical_id, target.stage),
                     (provider.name, physical_id, stage))
    case.assertGreaterEqual(target.runtime_index, 0)


def check_scan(case, scan, source):
    case.assertEqual(scan.run.source_id, source.id)
    case.assertTrue(all(turn.voice.run_id == scan.run.id for turn in scan.turns))


def check_transcript(case, transcript, source):
    case.assertEqual(transcript.run.source_id, source.id)
    case.assertTrue(all(segment.run_id == transcript.run.id for segment in transcript.segments))
