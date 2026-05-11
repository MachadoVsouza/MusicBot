from langchain_core.tools import tool
from app.spotify.service import SpotifyService
from app.spotify.repository import SpotifyRepository


def make_spotify_tools(token: str):
    svc = SpotifyService(SpotifyRepository(token))

    @tool
    def buscar_musica(query: str) -> dict:
        """
        Busca uma música no Spotify.
        Use quando o usuário pedir para buscar, tocar, ouvir ou encontrar uma música.
        query: nome da música e/ou artista. Ex: 'Creep Radiohead', 'Bohemian Rhapsody Queen'
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
        Retorna as músicas ouvidas recentemente pelo usuário no Spotify.
        Use quando o usuário perguntar o que ouviu recentemente, histórico de músicas, etc.
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
        Retorna as músicas mais ouvidas pelo usuário no Spotify.
        Use quando o usuário perguntar suas músicas favoritas, mais ouvidas, top tracks, etc.
        periodo: 'short_term' (últimas 4 semanas), 'medium_term' (6 meses), 'long_term' (todos os tempos)
        """
        tracks = svc.get_top_tracks(time_range=periodo)
        if not tracks:
            return {"erro": "Não foi possível buscar as top músicas."}
        return {"periodo": periodo, "tracks": [{"nome": t["name"], "artista": t["artist"]} for t in tracks]}

    @tool
    def top_artistas(periodo: str = "medium_term") -> dict:
        """
        Retorna os artistas mais ouvidos pelo usuário no Spotify.
        Use quando o usuário perguntar seus artistas favoritos, mais ouvidos, etc.
        periodo: 'short_term' (últimas 4 semanas), 'medium_term' (6 meses), 'long_term' (todos os tempos)
        """
        artistas = svc.get_top_artists(time_range=periodo)
        if not artistas:
            return {"erro": "Não foi possível buscar os top artistas."}
        return {"periodo": periodo, "artistas": [a["name"] for a in artistas]}

    @tool
    def musicas_curtidas() -> dict:
        """
        Retorna as músicas curtidas (Liked Songs) pelo usuário no Spotify.
        Use quando o usuário perguntar sobre músicas salvas, curtidas ou favoritas.
        """
        tracks = svc.get_saved_tracks()
        if not tracks:
            return {"erro": "Não foi possível buscar as músicas curtidas."}
        return {"tracks": [{"nome": t["name"], "artista": t["artist"], "adicionada_em": t["added_at"]} for t in tracks]}

    @tool
    def listar_playlists() -> dict:
        """
        Retorna as playlists do usuário no Spotify.
        Use quando o usuário perguntar sobre suas playlists.
        """
        playlists = svc.get_playlists()
        if not playlists:
            return {"erro": "Não foi possível buscar as playlists."}
        return {"playlists": [{"id": p["id"], "nome": p["name"], "total": p["total"]} for p in playlists]}

    @tool
    def criar_playlist(nome: str, descricao: str = "", publica: bool = True) -> dict:
        """
        Cria uma nova playlist no Spotify para o usuário.
        Use quando o usuário pedir para criar uma playlist.
        nome: nome da playlist
        descricao: descrição opcional
        publica: True para pública, False para privada
        """
        resultado = svc.create_playlist(nome, descricao, publica)
        if not resultado:
            return {"erro": "Não foi possível criar a playlist."}
        return {"mensagem": f"Playlist '{nome}' criada com sucesso!", "id": resultado["id"], "url": resultado["url"]}

    @tool
    def adicionar_musica_playlist(playlist_id: str, query: str) -> dict:
        """
        Adiciona uma música a uma playlist existente do usuário.
        Use quando o usuário pedir para adicionar uma música a uma playlist.
        playlist_id: ID da playlist (obtido via listar_playlists)
        query: nome da música e artista para buscar. Ex: 'Creep Radiohead'
        """
        track = svc.search_track(query)
        if not track:
            return {"erro": f"Música '{query}' não encontrada."}
        sucesso = svc.add_tracks_to_playlist(playlist_id, [track["uri"]])
        if not sucesso:
            return {"erro": "Não foi possível adicionar a música à playlist."}
        return {"mensagem": f"'{track['name']}' adicionada à playlist com sucesso!", "musica": track["name"], "artista": ", ".join(track["artists"])}

    @tool
    def buscar_artista(nome: str) -> dict:
        """
        Busca informações sobre um artista no Spotify.
        Use quando o usuário perguntar sobre um artista específico.
        nome: nome do artista. Ex: 'Radiohead', 'Queen'
        """
        track = svc.search_track(f"artist:{nome}")
        if not track:
            return {"erro": f"Artista '{nome}' não encontrado."}
        return {"artista": ", ".join(track["artists"]), "musica_exemplo": track["name"], "album": track["album"], "url": track["external_urls"].get("spotify")}

    return [buscar_musica, musicas_recentes, top_musicas, top_artistas, musicas_curtidas, listar_playlists, criar_playlist, adicionar_musica_playlist, buscar_artista]