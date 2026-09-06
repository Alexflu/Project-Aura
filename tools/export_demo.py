"""Render the same local stage used by ProjectAura.exe; no invented feature footage."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from aura.showcase import Scene,DURATION,NARRATION,ASSETS
from aura.core import DEFAULT_LOOK


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default='artifacts/ProjectAura-0.6-demo.mp4')
    parser.add_argument('--fps',type=int,default=24)
    args=parser.parse_args()
    if not 12<=args.fps<=60:raise ValueError('Use 12–60 fps.')
    import imageio_ffmpeg
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
    scene=Scene(dict(DEFAULT_LOOK,outfit='stealth',hair='pixie',palette='violet'))
    audio=ASSETS/'tour-audio.wav'
    if not audio.exists():raise RuntimeError('Run create_tour_audio.py first.')
    cmd=[imageio_ffmpeg.get_ffmpeg_exe(),'-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','960x540',
         '-r',str(args.fps),'-i','pipe:0','-i',str(audio),'-c:v','libx264','-crf','18','-preset','medium',
         '-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-t',str(DURATION),'-movflags','+faststart',str(output)]
    log=output.with_suffix('.encode.log')
    with log.open('wb') as errors:
        process=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=errors)
        try:
            for i in range(DURATION*args.fps):
                process.stdin.write(scene.frame(i/args.fps).tobytes())
                if i%(args.fps*8)==0:print(f'Rendered {i//args.fps}/{DURATION} seconds',flush=True)
            process.stdin.close()
            if process.wait(timeout=120):raise RuntimeError(log.read_text())
        except BaseException:
            process.kill();process.wait();raise
    def stamp(t):return f'00:{t//60:02}:{t%60:02},000'
    captions='\n\n'.join(f'{i}\n{stamp(start)} --> {stamp(end)}\n{text}' for i,(start,end,text) in enumerate(NARRATION,1))
    output.with_suffix('.srt').write_text(captions+'\n',encoding='utf-8')
    scene.frame(10).save(output.with_suffix('.png'))
    digest=hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix('.mp4.sha256').write_text(f'{digest}  {output.name}\n')
    print(json.dumps(dict(video=str(output.resolve()),duration=DURATION,fps=args.fps,sha256=digest)))

if __name__=='__main__':main()
