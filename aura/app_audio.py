"""Opt-in per-session peak metering. No PCM capture, microphone or transcript access."""
import math
import os
from .core import AuraError


def sessions():
    if os.name!='nt':raise AuraError('Application audio levels require Windows.')
    from pycaw.pycaw import AudioUtilities
    from pycaw.api.audiopolicy import IAudioSessionControl2
    from pycaw.utils import AudioSession
    result=[]
    # Include active output devices so per-app audio routing is supported.
    for device in AudioUtilities.GetAllDevices(data_flow=0,device_state=1):
        try:
            listing=device.AudioSessionManager.GetSessionEnumerator()
            for index in range(listing.GetCount()):
                session=AudioSession(listing.GetSession(index).QueryInterface(IAudioSessionControl2))
                process=session.Process
                if process and process.pid!=os.getpid():
                    label=f'{process.name()} · {process.pid} · {device.FriendlyName}'
                    result.append((label,session,process.create_time()))
        except Exception:
            continue
    return result


class AppMeter:
    def __init__(self,session,created):
        from pycaw.api.endpointvolume import IAudioMeterInformation
        self.process=session.Process
        self.created=created
        self.meter=session._ctl.QueryInterface(IAudioMeterInformation)
        self.name=self.process.name()

    def level(self):
        try:
            if not self.process.is_running() or self.process.create_time()!=self.created:
                raise RuntimeError('Process ended')
            value=float(self.meter.GetPeakValue())
            if not math.isfinite(value):return 0
            return max(0,min(1,value*2.5))
        except Exception as exc:
            raise AuraError('Selected audio session ended. Refresh the app list to reconnect.') from exc
