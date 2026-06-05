"""
MCP Server — expõe as tools do Spotify como ferramentas MCP para Claude Desktop, Insomnia, etc.
 
Para testar:
  python -m app.mcp_server
 
Para usar com Claude Desktop, adicione no claude_desktop_config.json:
  {
    "mcpServers": {
      "musicbot": {
        "command": "python",
        "args": ["-m", "app.mcp_server"],
        "env": {
          "SPOTIFY_CLIENT_ID": "...",
          "SPOTIFY_CLIENT_SECRET": "..."
        }
      }
    }
  }
"""
import os
import sys
import json
import logging
from typing import Any

# Adiciona o diretório raiz ao path se executado standalone
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

from app.spotify.service import SpotifyService
from app.spotify.repository import SpotifyRepository

logger = logging.getLogger(__name__)

# Cache do token — em produção usar refresh flow
_token: str | None = None
_device_id: str | None = None


def _get_svc() -> SpotifyService:
    global _token
    if not _token:
        # Tenta pegar do env ou usa token vazio (vai falhar na primeira chamada)
        _token = os.getenv("SPOTIFY_ACCESS_TOKEN", "")
    return SpotifyService(SpotifyRepository(_token))


server = Server("musicbot-mcp")


def _result(msg: str) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=msg)]


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="buscar_musica",
            description="Busca uma música no Spotify pelo nome e/ou artista",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Nome da música e/ou artista"}
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="tocar_musica",
            description="Toca uma música no Spotify agora",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Nome da música"},
                    "dispositivo": {"type": "string", "description": "Nome do dispositivo (opcional)"},
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="pausar_musica",
            description="Pausa a música que está tocando",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="proxima_faixa",
            description="Pula para a próxima faixa",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="faixa_anterior",
            description="Volta para a faixa anterior",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="listar_dispositivos",
            description="Lista os dispositivos disponíveis",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="mudar_dispositivo",
            description="Muda o playback para um dispositivo específico",
            inputSchema={
                "type": "object",
                "properties": {
                    "nome_dispositivo": {"type": "string", "description": "Nome do dispositivo"}
                },
                "required": ["nome_dispositivo"],
            },
        ),
        types.Tool(
            name="adicionar_fila",
            description="Adiciona uma música na fila de reprodução",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Nome da música"}
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="listar_playlists",
            description="Lista as playlists do usuário",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="criar_playlist",
            description="Cria uma nova playlist",
            inputSchema={
                "type": "object",
                "properties": {
                    "nome": {"type": "string"},
                    "descricao": {"type": "string"},
                    "publica": {"type": "boolean"},
                },
                "required": ["nome"],
            },
        ),
        types.Tool(
            name="buscar_artista",
            description="Busca informações sobre um artista",
            inputSchema={
                "type": "object",
                "properties": {
                    "nome": {"type": "string"}
                },
                "required": ["nome"],
            },
        ),
        types.Tool(
            name="musicas_recentes",
            description="Retorna as últimas músicas ouvidas",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="top_musicas",
            description="Retorna as músicas mais ouvidas",
            inputSchema={
                "type": "object",
                "properties": {
                    "periodo": {
                        "type": "string",
                        "enum": ["short_term", "medium_term", "long_term"],
                        "description": "short_term=4semanas, medium_term=6meses, long_term=tudo"
                    }
                },
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    global _device_id
    args = arguments or {}
    svc = _get_svc()

    try:
        if name == "buscar_musica":
            track = svc.search_track(args["query"])
            if not track:
                return _result(f"Nenhuma música encontrada para '{args['query']}'")
            return _result(json.dumps(track, indent=2, ensure_ascii=False))

        elif name == "tocar_musica":
            track = svc.search_track(args["query"])
            if not track:
                return _result(f"Música '{args['query']}' não encontrada.")
            # Resolve dispositivo
            dispositivo = args.get("dispositivo")
            device_id = _device_id
            if dispositivo:
                devices = svc.get_devices()
                for d in devices:
                    if dispositivo.lower() in d["name"].lower() or dispositivo.lower() in d["type"].lower():
                        device_id = d["id"]
                        break
            resultado = svc.play_track(track["uri"], device_id)
            return _result(resultado.get("mensagem", resultado.get("erro", "OK")))

        elif name == "pausar_musica":
            resultado = svc.pause(_device_id)
            return _result(resultado.get("mensagem", "OK"))

        elif name == "proxima_faixa":
            resultado = svc.next(_device_id)
            return _result(resultado.get("mensagem", "OK"))

        elif name == "faixa_anterior":
            resultado = svc.previous(_device_id)
            return _result(resultado.get("mensagem", "OK"))

        elif name == "listar_dispositivos":
            devices = svc.get_devices()
            if not devices:
                return _result("Nenhum dispositivo encontrado.")
            lines = []
            for d in devices:
                ativo = " ✅ ativo" if d.get("is_active") else ""
                lines.append(f"  • {d['name']} ({d['type']}){ativo} — ID: {d['id']}")
            return _result("Dispositivos disponíveis:\n" + "\n".join(lines))

        elif name == "mudar_dispositivo":
            nome = args["nome_dispositivo"]
            devices = svc.get_devices()
            encontrado = None
            for d in devices:
                if nome.lower() in d["name"].lower() or nome.lower() in d["type"].lower():
                    encontrado = d
                    break
            if not encontrado:
                return _result(f"Dispositivo '{nome}' não encontrado.")
            resultado = svc.transfer_to_device(encontrado["id"])
            if resultado.get("ok"):
                _device_id = encontrado["id"]
            return _result(resultado.get("mensagem", resultado.get("erro", "OK")))

        elif name == "adicionar_fila":
            track = svc.search_track(args["query"])
            if not track:
                return _result(f"Música '{args['query']}' não encontrada.")
            resultado = svc.add_to_queue(track["uri"], _device_id)
            return _result(resultado.get("mensagem", resultado.get("erro", "OK")))

        elif name == "listar_playlists":
            playlists = svc.get_playlists()
            if not playlists:
                return _result("Nenhuma playlist encontrada.")
            lines = [f"  • {p['name']} ({p['total']} músicas) — ID: {p['id']}" for p in playlists]
            return _result("Playlists:\n" + "\n".join(lines))

        elif name == "criar_playlist":
            resultado = svc.create_playlist(args["nome"], args.get("descricao", ""), args.get("publica", True))
            if resultado.get("id"):
                return _result(f"Playlist '{args['nome']}' criada! {resultado['url']}")
            return _result("Erro ao criar playlist.")

        elif name == "buscar_artista":
            artista = svc.get_artist_info(args["nome"])
            if not artista:
                return _result(f"Artista '{args['nome']}' não encontrado.")
            return _result(json.dumps(artista, indent=2, ensure_ascii=False))

        elif name == "musicas_recentes":
            tracks = svc.get_recently_played()
            if not tracks:
                return _result("Nenhuma música encontrada.")
            return _result(json.dumps(tracks[:5], indent=2, ensure_ascii=False))

        elif name == "top_musicas":
            periodo = args.get("periodo", "medium_term")
            tracks = svc.get_top_tracks(time_range=periodo)
            if not tracks:
                return _result("Nenhuma música encontrada.")
            return _result(json.dumps(tracks, indent=2, ensure_ascii=False))

        else:
            return _result(f"Ferramenta desconhecida: {name}")

    except Exception as e:
        logger.exception(f"Erro na tool {name}")
        return _result(f"Erro: {str(e)}")


async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="musicbot-mcp",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())