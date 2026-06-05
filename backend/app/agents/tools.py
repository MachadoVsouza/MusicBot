import requests
from langchain_core.tools import tool
from app.spotify.service import SpotifyService
from app.spotify.repository import SpotifyRepository


def make_spotify_tools(token: str):
    svc = SpotifyService(SpotifyRepository(token))

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
            "duracao_ms":  track["duration_ms"],
        }

    @tool
    def musicas_recentes() -> dict:
        """
        Retorna as últimas músicas ouvidas pelo usuário no Spotify.
        Use quando perguntar sobre histórico recente, o que ouviu hoje/essa semana.
        """
        tracks = svc.get_recently_played()
        if not tracks:
            return {"erro": "Não foi possível buscar o histórico recente."}
        return {
            "tracks": [
                {"nome": t["name"], "artista": t["artist"], "album": t["album"], "ouvida_em": t["played_at"]}
                for t in tracks[:10]
            ]
        }

    @tool
    def top_musicas(periodo: str = "medium_term") -> dict:
        """
        Retorna as músicas mais ouvidas pelo usuário.
        Use quando perguntar sobre favoritas, mais ouvidas, top tracks.
        periodo: 'short_term' (4 semanas), 'medium_term' (6 meses), 'long_term' (tudo)
        """
        tracks = svc.get_top_tracks(time_range=periodo)
        if not tracks:
            return {"erro": "Não foi possível buscar as top músicas."}
        return {
            "periodo": periodo,
            "tracks":  [{"nome": t["name"], "artista": t["artist"]} for t in tracks],
        }

    @tool
    def top_artistas(periodo: str = "medium_term") -> dict:
        """
        Retorna os artistas mais ouvidos pelo usuário.
        Use quando perguntar sobre artistas favoritos, mais ouvidos.
        periodo: 'short_term' (4 semanas), 'medium_term' (6 meses), 'long_term' (tudo)
        """
        artistas = svc.get_top_artists(time_range=periodo)
        if not artistas:
            return {"erro": "Não foi possível buscar os top artistas."}
        return {
            "periodo":  periodo,
            "artistas": [{"nome": a["name"], "generos": a.get("genres", [])} for a in artistas],
        }

    @tool
    def musicas_curtidas() -> dict:
        """
        Retorna as músicas curtidas (Liked Songs) pelo usuário.
        Use quando perguntar sobre músicas salvas, curtidas ou favoritadas.
        """
        tracks = svc.get_saved_tracks()
        if not tracks:
            return {"erro": "Não foi possível buscar as músicas curtidas."}
        return {
            "tracks": [
                {"nome": t["name"], "artista": t["artist"], "adicionada_em": t["added_at"]}
                for t in tracks
            ]
        }

    @tool
    def listar_playlists() -> dict:
        """
        Retorna as playlists do usuário no Spotify.
        Use quando perguntar sobre playlists, ou antes de adicionar música a uma playlist.
        """
        playlists = svc.get_playlists()
        if not playlists:
            return {"erro": "Não foi possível buscar as playlists."}
        return {
            "playlists": [{"id": p["id"], "nome": p["name"], "total_musicas": p["total"]} for p in playlists]
        }

    @tool
    def criar_playlist(nome: str, descricao: str = "", publica: bool = True) -> dict:
        """
        Cria uma nova playlist no Spotify para o usuário.
        Use quando o usuário pedir explicitamente para criar uma playlist.
        """
        resultado = svc.create_playlist(nome, descricao, publica)
        if not resultado:
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

    @tool
    def tocar_musica(query: str, device_id: str | None = None) -> dict:
        """
        Toca uma música no Spotify em tempo real.
        Use quando o usuário pedir para tocar, ouvir, dar play em uma música específica.
        Exemplos: 'toca Creep do Radiohead', 'quero ouvir Bohemian Rhapsody'
        Primeiro busca a música, depois inicia o playback no dispositivo Spotify do usuário.
        Se device_id não for informado, usa o dispositivo ativo.
        """
        track = svc.search_track(query)
        if not track:
            return {"erro": f"Música '{query}' não encontrada."}
        return svc.play_track(track["uri"], device_id)

    @tool
    def tocar_playlist(playlist_id: str, device_id: str | None = None) -> dict:
        """
        Toca uma playlist inteira no Spotify.
        Use quando o usuário pedir para tocar uma playlist específica.
        O playlist_id pode ser obtido com listar_playlists.
        """
        return svc.play_context(f"spotify:playlist:{playlist_id}", device_id)

    @tool
    def pausar_musica(device_id: str | None = None) -> dict:
        """
        Pausa a música que está tocando no Spotify.
        Use quando o usuário pedir para pausar, parar a música.
        """
        return svc.pause(device_id)

    @tool
    def proxima_faixa(device_id: str | None = None) -> dict:
        """
        Pula para a próxima faixa no Spotify.
        Use quando o usuário pedir para pular, avançar, próxima música.
        """
        return svc.next(device_id)

    @tool
    def faixa_anterior(device_id: str | None = None) -> dict:
        """
        Volta para a faixa anterior no Spotify.
        Use quando o usuário pedir para voltar, música anterior.
        """
        return svc.previous(device_id)

    @tool
    def listar_dispositivos() -> dict:
        """
        Lista os dispositivos disponíveis para playback no Spotify.
        Use quando o usuário perguntar onde está tocando, ou se não encontrar dispositivo ativo.
        """
        devices = svc.get_devices()
        if not devices:
            return {"erro": "Nenhum dispositivo encontrado. Abra o Spotify em algum dispositivo."}
        return {
            "dispositivos": [
                {"id": d["id"], "nome": d["name"], "tipo": d["type"], "ativo": d.get("is_active", False)}
                for d in devices
            ]
        }

    @tool
    def buscar_artista(nome: str) -> dict:
        """
        Busca informações sobre um artista no Spotify: bio, gêneros, popularidade e músicas populares.
        Use quando o usuário perguntar sobre um artista específico.
        """
        import requests as req
        headers = {"Authorization": f"Bearer {token}"}

        # Busca o artista
        r = req.get(
            "https://api.spotify.com/v1/search",
            headers=headers,
            params={"q": nome, "type": "artist", "limit": 1},
            timeout=10,
        )
        if not r.ok or not r.json()["artists"]["items"]:
            return {"erro": f"Artista '{nome}' não encontrado."}

        artista = r.json()["artists"]["items"][0]
        artista_id = artista["id"]

        # Busca top tracks
        r2 = req.get(
            f"https://api.spotify.com/v1/artists/{artista_id}/top-tracks",
            headers=headers,
            params={"market": "BR"},
            timeout=10,
        )
        top_tracks = []
        if r2.ok:
            top_tracks = [t["name"] for t in r2.json().get("tracks", [])[:5]]

        return {
            "nome":         artista["name"],
            "generos":      artista.get("genres", []),
            "popularidade": artista.get("popularity"),
            "seguidores":   artista["followers"]["total"],
            "top_musicas":  top_tracks,
            "url":          artista["external_urls"].get("spotify"),
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
        tocar_musica,
        tocar_playlist,
        pausar_musica,
        proxima_faixa,
        faixa_anterior,
        listar_dispositivos,
    ]
