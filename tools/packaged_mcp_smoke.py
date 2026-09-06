"""SDK round trip against the actual portable bridge, using a disposable profile."""
import asyncio
import json
from pathlib import Path
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from aura.core import Store

async def main():
    with tempfile.TemporaryDirectory() as temp:
        store=Store(Path(temp)/'state.db')
        params=StdioServerParameters(command=str(Path(sys.argv[1]).resolve()),args=['--data',str(store.path)])
        async with stdio_client(params) as (read,write):
            async with ClientSession(read,write) as client:
                await client.initialize()
                listing=await client.list_tools()
                assert len(listing.tools)==6
                denied=await client.call_tool('aura_status',{})
                assert denied.is_error
                store.preferences([], 'violet',False,True,False,False)
                result=await client.call_tool('aura_propose_cue',{'cue':'draw'})
                assert not result.is_error,result
                request=json.loads(result.content[0].text)
                assert store.pending()[0]['id']==request['request_id']
                observed=[]
                store.resolve(request['request_id'],True,lambda _:None,lambda p:observed.append(p) or 'started')
                status=await client.call_tool('aura_request_status',{'request_id':request['request_id']})
                assert json.loads(status.content[0].text)['status']=='submitted'
                assert observed==[{'cue':'draw'}]
    print('Portable MCP passed: six tools, disabled gate, queued cue, local approval, status round trip, clean exit.')

if __name__=='__main__':asyncio.run(main())
