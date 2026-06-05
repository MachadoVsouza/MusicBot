from langchain_core.tools import tool
from app.spotify.service import SpotifyService
from app.spotify.repository import SpotifyRepository


def make_spotify_tools(token: str):
    svc = SpotifyService(SpotifyRepository(token))

    # ── Busca ─────────────────────────────────────────────────────────────────

    @tool
    def buscar_musica(query: str) -> dict:
        """
        Busca uma música no Spotify pelo nome e/ou artista.
        Use quando o usuário pedir para buscar, tocar, ouvir ou encontrar uma música.
        Exemplos de query: 'Creep Radiohead', 'Bohemian Rhapsody Queen', 'Shape of You'
        """
        track = svc.search_track(query)
        if not track:
            return {"erro": f"Nenhuma música encontrada para '{query}'"}
        return {
            "nome":        track["name"],
            "artista":     ", ".join(track["artists"]),
            "album":       track["album"],
            "preview_url": track.get("preview_url"),
            "url":         track["external_urls"].get("spotify"),
            "uri":         track["uri"],
            "duracao_ms":  track["duration_ms"],
        }

    @tool
    def musicas_recentes() -> dict:
        """Retorna as últimas músicas ouvidas pelo usuário no Spotify."""
        tracks = svc.get_recently_played()
        if not tracks:
            return {"erro": "Não foi possível buscar o histórico recente."}
        return {
            "tracks": [
                {"nome": t["name"], "artista": t["artist"], "album": t["album"],
                 "ouvida_em": t["played_at"], "spotify_url": t.get("spotify_url")}
                for t in tracks[:10]
            ]
        }

    @tool
    def top_musicas(periodo: str = "medium_term") -> dict:
        """
        Retorna as músicas mais ouvidas pelo usuário.
        periodo: 'short_term' (4 semanas), 'medium_term' (6 meses), 'long_term' (tudo)
        """
        tracks = svc.get_top_tracks(time_range=periodo)
        if not tracks:
            return {"erro": "Não foi possível buscar as top músicas."}
        return {"periodo": periodo, "tracks": tracks}

    @tool
    def top_artistas(periodo: str = "medium_term") -> dict:
        """
        Retorna os artistas mais ouvidos pelo usuário.
        periodo: 'short_term' (4 semanas), 'medium_term' (6 meses), 'long_term' (tudo)
        """
        artistas = svc.get_top_artists(time_range=periodo)
        if not artistas:
            return {"erro": "Não foi possível buscar os top artistas."}
        return {"periodo": periodo, "artistas": artistas}

    @tool
    def musicas_curtidas() -> dict:
        """Retorna as músicas curtidas (Liked Songs) pelo usuário."""
        tracks = svc.get_saved_tracks()
        if not tracks:
            return {"erro": "Não foi possível buscar as músicas curtidas."}
        return {"tracks": tracks}

    @tool
    def listar_playlists() -> dict:
        """Retorna as playlists do usuário no Spotify."""
        playlists = svc.get_playlists()
        if not playlists:
            return {"erro": "Não foi possível buscar as playlists."}
        return {"playlists": playlists}

    @tool
    def buscar_artista(nome: str) -> dict:
        """
        Busca informações sobre um artista no Spotify: bio, gêneros, popularidade e músicas populares.
        Use quando o usuário perguntar sobre um artista específico.
        """
        artista = svc.get_artist_info(nome)
        if not artista:
            return {"erro": f"Artista '{nome}' não encontrado."}
        return artista

    # ── Playlists (write) ─────────────────────────────────────────────────────

    @tool
    def criar_playlist(nome: str, descricao: str = "", publica: bool = True) -> dict:
        """
        Cria uma nova playlist no Spotify para o usuário.
        Use quando o usuário pedir explicitamente para criar uma playlist.
        """
        resultado = svc.create_playlist(nome, descricao, publica)
        if not resultado.get("id"):
            return {"erro": "Não foi possível criar a playlist."}
        return {
            "mensagem": f"Playlist '{nome}' criada com sucesso!",
            "id":       resultado["id"],
            "url":      resultado["url"],
        }

    @tool
    def adicionar_musica_playlist(playlist_id: str, query: str) -> dict:
        """
        Adiciona uma música a uma playlist existente.
        Use quando o usuário pedir para adicionar uma música a uma playlist.
        Chame listar_playlists primeiro para obter o playlist_id se necessário.
        """
        track = svc.search_track(query)
        if not track:
            return {"erro": f"Música '{query}' não encontrada."}
        sucesso = svc.add_tracks_to_playlist(playlist_id, [track["uri"]])
        if not sucesso:
            return {"erro": "Não foi possível adicionar a música à playlist."}
        return {
            "mensagem": f"'{track['name']}' adicionada com sucesso!",
            "musica":   track["name"],
            "artista":  ", ".join(track["artists"]),
        }

    @tool(return_direct=True)
    def criar_playlist_inteligente(musicas: list[str], nome: str, descricao: str = "") -> str:
        """
        CRIA UMA PLAYLIST AUTOMATICAMENTE a partir de uma lista de nomes de músicas e artistas.
        Recebe uma lista de strings no formato "Artista - Música" ou "nome da música" e cria a playlist.
        Exemplo: musicas=["Radiohead - Creep", "Bohemian Rhapsody", "Nirvana - Smells Like Teen Spirit"]
        """
        uris = []
        erros = []
        for item in musicas:
            track = svc.search_track(item)
            if track:
                uris.append(track["uri"])
            else:
                erros.append(item)

        resultado = svc.create_playlist(nome, descricao)
        if not resultado.get("id"):
            return f"Não foi possível criar a playlist '{nome}'."

        if uris:
            svc.add_tracks_to_playlist(resultado["id"], uris)

        msg = f"✅ Playlist '{nome}' criada! Link: {resultado['url']}\n"
        msg += f"🎵 {len(uris)} músicas adicionadas.\n"
        if erros:
            msg += f"⚠️ {len(erros)} música(s) não encontrada(s): {', '.join(erros[:5])}"
        return msg

    # ── Playback ──────────────────────────────────────────────────────────────

    def _resolver_dispositivo(nome: str | None) -> str | None:
        """Se for um nome de dispositivo (não ID), tenta encontrar pelo nome."""
        if not nome or nome.startswith("spotify:") or ":" in nome:
            return nome  # já é um ID ou URI
        devices = svc.get_devices()
        nome_lower = nome.lower().strip()
        for d in devices:
            if nome_lower in d["name"].lower() or nome_lower in d["type"].lower():
                return d["id"]
        return nome  # não encontrou, retorna como veio

    @tool(return_direct=True)
    def tocar_musica(query: str, dispositivo: str | None = None) -> str:
        """
        TOCA UMA MÚSICA NO SPOTIFY AGORA.
        Use quando o usuário pedir para tocar, ouvir, dar play em uma música específica.
        Se o usuário mencionar um dispositivo (ex: "no celular", "na caixa de som"), passe o nome do dispositivo.
        Primeiro busca a música, depois inicia o playback.
        """
        track = svc.search_track(query)
        if not track:
            return f"Não encontrei a música '{query}'."
        device_id = _resolver_dispositivo(dispositivo) if dispositivo else None
        resultado = svc.play_track(track["uri"], device_id)
        return resultado.get("mensagem", resultado.get("erro", "OK"))

    @tool(return_direct=True)
    def tocar_playlist(playlist_id: str, dispositivo: str | None = None) -> str:
        """
        TOCA UMA PLAYLIST INTEIRA NO SPOTIFY AGORA.
        Use quando o usuário pedir para tocar uma playlist específica.
        O playlist_id pode ser obtido com listar_playlists.
        Se o usuário mencionar um dispositivo (ex: "no celular"), passe o nome do dispositivo.
        """
        device_id = _resolver_dispositivo(dispositivo) if dispositivo else None
        resultado = svc.play_context(f"spotify:playlist:{playlist_id}", device_id)
        return resultado.get("mensagem", resultado.get("erro", "OK"))

    @tool(return_direct=True)
    def pausar_musica(device_id: str | None = None) -> str:
        """PAUSA A MÚSICA QUE ESTÁ TOCANDO NO SPOTIFY AGORA."""
        resultado = svc.pause(device_id)
        return resultado.get("mensagem", resultado.get("erro", "OK"))

    @tool(return_direct=True)
    def proxima_faixa(device_id: str | None = None) -> str:
        """PULA PARA A PRÓXIMA FAIXA NO SPOTIFY."""
        resultado = svc.next(device_id)
        return resultado.get("mensagem", resultado.get("erro", "OK"))

    @tool(return_direct=True)
    def faixa_anterior(device_id: str | None = None) -> str:
        """VOLTA PARA A FAIXA ANTERIOR NO SPOTIFY."""
        resultado = svc.previous(device_id)
        return resultado.get("mensagem", resultado.get("erro", "OK"))

    @tool(return_direct=True)
    def adicionar_fila(query: str, device_id: str | None = None) -> str:
        """
        ADICIONA UMA MÚSICA NA FILA DE REPRODUÇÃO DO SPOTIFY.
        A música será tocada após a atual terminar.
        Use quando o usuário pedir para adicionar na fila, tocar depois, ouvir em seguida.
        """
        track = svc.search_track(query)
        if not track:
            return f"Não encontrei a música '{query}'."
        resultado = svc.add_to_queue(track["uri"], device_id)
        return resultado.get("mensagem", resultado.get("erro", "OK"))

    @tool(return_direct=True)
    def adicionar_lista_fila(musicas: list[str], device_id: str | None = None) -> str:
        """
        ADICIONA VÁRIAS MÚSICAS NA FILA DO SPOTIFY DE UMA SÓ VEZ.
        Recebe uma lista de strings com nomes de músicas/artistas.
        Exemplo: musicas=["Bohemian Rhapsody", "Stairway to Heaven", "Hotel California"]
        """
        adicionadas = 0
        erros = []
        for item in musicas:
            track = svc.search_track(item)
            if track:
                svc.add_to_queue(track["uri"], device_id)
                adicionadas += 1
            else:
                erros.append(item)

        msg = f"✅ {adicionadas} música(s) adicionada(s) à fila!\n"
        if erros:
            msg += f"⚠️ {len(erros)} música(s) não encontrada(s): {', '.join(erros[:5])}"
        return msg

    @tool(return_direct=True)
    def mudar_dispositivo(nome_dispositivo: str) -> str:
        """
        MUDA O PLAYBACK PARA UM DISPOSITIVO ESPECÍFICO.
        Use quando o usuário pedir para mudar de dispositivo, tipo "toca no celular", "muda pra caixa de som", "toca no pc".
        Primeiro lista os dispositivos, encontra o que o usuário pediu, e transfere o playback.
        """
        devices = svc.get_devices()
        if not devices:
            return "Nenhum dispositivo encontrado. Abra o Spotify em algum dispositivo primeiro."

        nome_busca = nome_dispositivo.lower().strip()
        device = None

        # Tenta encontrar por nome exato
        for d in devices:
            if nome_busca in d["name"].lower() or nome_busca in d["type"].lower():
                device = d
                break

        if not device:
            lista = "\n".join(f"  • {d['name']} ({d['type']}) {'✅ ativo' if d.get('is_active') else ''}" for d in devices)
            return f"Dispositivo '{nome_dispositivo}' não encontrado. Disponíveis:\n{lista}"

        resultado = svc.transfer_to_device(device["id"])
        return resultado.get("mensagem", resultado.get("erro", f"✅ Playback transferido para {device['name']}!"))

    @tool
    def listar_dispositivos() -> dict:
        """Lista os dispositivos disponíveis para playback no Spotify."""
        devices = svc.get_devices()
        if not devices:
            return {"erro": "Nenhum dispositivo encontrado. Abra o Spotify em algum dispositivo."}
        return {
            "dispositivos": [
                {"id": d["id"], "nome": d["name"], "tipo": d["type"], "ativo": d.get("is_active", False)}
                for d in devices
            ]
        }

    return [
        buscar_musica,
        musicas_recentes,
        top_musicas,
        top_artistas,
        musicas_curtidas,
        listar_playlists,
        criar_playlist,
        adicionar_musica_playlist,
        buscar_artista,
        # Playback tools (return_direct)
        tocar_musica,
        tocar_playlist,
        pausar_musica,
        proxima_faixa,
        faixa_anterior,
        adicionar_fila,
        adicionar_lista_fila,
        mudar_dispositivo,
        listar_dispositivos,
        # Smart playlist
        criar_playlist_inteligente,
    ]
