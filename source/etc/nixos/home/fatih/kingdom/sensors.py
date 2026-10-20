import asyncio
from common import RUNTIME,STATE,atomic,load,settings

async def watch():
    from dbus_next.aio import MessageBus
    from dbus_next import BusType
    bus=None
    try:
        bus=await MessageBus(bus_type=BusType.SYSTEM).connect()
        intro=await bus.introspect('net.hadess.SensorProxy','/net/hadess/SensorProxy')
        obj=bus.get_proxy_object('net.hadess.SensorProxy','/net/hadess/SensorProxy',intro)
        sensor=obj.get_interface('net.hadess.SensorProxy');props=obj.get_interface('org.freedesktop.DBus.Properties')
        async def update():
            rows=await props.call_get_all('net.hadess.SensorProxy')
            atomic(RUNTIME/'orientation.json',dict(available=rows['HasAccelerometer'].value,orientation=rows['AccelerometerOrientation'].value))
        def changed(interface,changes,invalidated):
            if interface=='net.hadess.SensorProxy':asyncio.create_task(update())
        props.on_properties_changed(changed)
        claimed=False
        try:
            while True:
                prefs=settings()['tablet'];physical=load('/run/yoga-tablet/state.json').get('tablet',False)
                override=load(STATE/'local.json').get('tabletOverride')
                mode=(physical if prefs['automatic'] else False) if override is None else bool(override)
                needed=mode and prefs['rotation']
                if needed and not claimed:await sensor.call_claim_accelerometer();claimed=True
                elif claimed and not needed:await sensor.call_release_accelerometer();claimed=False
                await update();await asyncio.sleep(2)
        finally:
            if claimed:await sensor.call_release_accelerometer()
    except Exception:atomic(RUNTIME/'orientation.json',dict(available=False,orientation='normal'))
    finally:
        if bus:bus.disconnect()
