"""Exercise a selected process meter with a muted disposable render session."""
import os,sys,time,subprocess,tempfile,wave,math
import psutil
from pathlib import Path
from array import array
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

if '--worker' in sys.argv:
    import winsound
    winsound.PlaySound(sys.argv[-1],winsound.SND_FILENAME|winsound.SND_ASYNC)
    time.sleep(9)
    raise SystemExit()

from pycaw.pycaw import AudioUtilities
from aura.app_audio import AppMeter,sessions
with tempfile.TemporaryDirectory() as temp:
    path=Path(temp)/'test.wav';rate=22050
    pcm=array('h',[0])*(rate*5)
    pcm.extend(round(math.sin(i*math.tau*330/rate)*5000) for i in range(rate*3))
    with wave.open(str(path),'wb') as output:
        output.setnchannels(1);output.setsampwidth(2);output.setframerate(rate);output.writeframes(pcm.tobytes())
    child=subprocess.Popen([sys.executable,__file__,'--worker',str(path)],creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        chosen=None;workers=[];deadline=time.monotonic()+3
        while time.monotonic()<deadline and chosen is None:
            workers=psutil.Process(child.pid).children(recursive=True)
            worker_ids={child.pid, *(p.pid for p in workers)}
            for _,session,_ in sessions():
                if session.Process and session.Process.pid in worker_ids:chosen=session;break
            time.sleep(.05)
        assert chosen is not None,'No disposable audio session was created.'
        # Only our worker's session is muted, before its initial silence ends.
        chosen.SimpleAudioVolume.SetMute(1,None)
        meter=AppMeter(chosen,chosen.Process.create_time())
        levels=[];deadline=time.monotonic()+6
        while time.monotonic()<deadline:
            levels.append(meter.level());time.sleep(.03)
        assert max(levels)>.03, max(levels)
        assert min(levels)<.001
        print('Live app meter passed: selected muted worker, silence and nonzero signal, no PCM capture; peak',round(max(levels),3))
    finally:
        for worker in workers:
            try:worker.terminate()
            except psutil.NoSuchProcess:pass
        psutil.wait_procs(workers,timeout=3)
        if child.poll() is None:child.terminate()
        child.wait(timeout=5)
