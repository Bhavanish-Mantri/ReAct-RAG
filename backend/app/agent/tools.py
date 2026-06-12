import logging
import json
import requests
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from backend.app.config import settings

logger = logging.getLogger(__name__)

# --- Mock Movies Database for Fallback and Keyless Execution ---
MOCK_MOVIES_DB = [
    {
        "title": "Scream",
        "release_date": "1996-12-20",
        "release_year": 1996,
        "genres": ["Horror", "Mystery"],
        "certification": "R",
        "rating": 7.4,
        "watch_providers": ["Paramount Plus", "Max", "Hulu"],
        "overview": "A year after the murder of her mother, a teenage girl is terrorized by a new killer, who targets the girl and her friends by using horror films as part of a deadly game.",
        "poster_path": "/kqjL1v05HgDZ9RjLYC6K2qw7j2S.jpg"
    },
    {
        "title": "The Silence of the Lambs",
        "release_date": "1991-02-14",
        "release_year": 1991,
        "genres": ["Horror", "Thriller", "Crime"],
        "certification": "R",
        "rating": 8.5,
        "watch_providers": ["Amazon Prime Video", "MGM Plus"],
        "overview": "A young FBI cadet must receive the help of an incarcerated and manipulative cannibal killer to help catch another serial killer, a madman who skins his victims.",
        "poster_path": "/jxO1t4kvt214JYYK1ImJe3bUrrY.jpg"
    },
    {
        "title": "The Blair Witch Project",
        "release_date": "1999-07-30",
        "release_year": 1999,
        "genres": ["Horror", "Mystery"],
        "certification": "R",
        "rating": 6.3,
        "watch_providers": ["Peacock", "Hulu", "Amazon Prime Video"],
        "overview": "Three film students vanish after traveling into a Maryland forest to film a documentary on the local Blair Witch legend, leaving only their footage behind.",
        "poster_path": "/9tUeNvy24U75k4yUvL59A1T4n89.jpg"
    },
    {
        "title": "The Shining",
        "release_date": "1980-05-23",
        "release_year": 1980,
        "genres": ["Horror", "Thriller"],
        "certification": "R",
        "rating": 8.2,
        "watch_providers": ["Max", "Amazon Prime Video"],
        "overview": "A family heads to an isolated hotel for the winter where a sinister presence influences the father into violence, while his psychic son sees horrific forebodings from both past and future.",
        "poster_path": "/x4ka2402h2w6Q28c4586tbA2qjB.jpg"
    },
    {
        "title": "The Conjuring",
        "release_date": "2013-07-19",
        "release_year": 2013,
        "genres": ["Horror", "Thriller", "Mystery"],
        "certification": "R",
        "rating": 7.5,
        "watch_providers": ["Netflix", "Max", "Amazon Prime Video"],
        "overview": "Paranormal investigators Ed and Lorraine Warren work to help a family terrorized by a dark presence in their farmhouse.",
        "poster_path": "/wTIrbG22596KUJbhali40a4xtWZ.jpg"
    },
    {
        "title": "Get Out",
        "release_date": "2017-02-24",
        "release_year": 2017,
        "genres": ["Horror", "Thriller", "Mystery"],
        "certification": "R",
        "rating": 7.6,
        "watch_providers": ["Peacock", "Amazon Prime Video"],
        "overview": "A young Afro-American visits his white girlfriend's parents for the weekend, where his simmering uneasiness about their reception eventually reaches a boiling point.",
        "poster_path": "/tEx6xyWvWQJZypk31I065CcJUrR.jpg"
    },
    {
        "title": "Jurassic Park",
        "release_date": "1993-06-11",
        "release_year": 1993,
        "genres": ["Adventure", "Science Fiction"],
        "certification": "PG-13",
        "rating": 8.1,
        "watch_providers": ["Netflix", "Amazon Prime Video"],
        "overview": "A pragmatic paleontologist visiting an almost complete theme park is tasked with protecting a couple of kids after a power failure causes the park's cloned dinosaurs to run loose.",
        "poster_path": "/o9Q51iC1l3b1236.jpg"
    },
    {
        "title": "The Matrix",
        "release_date": "1999-03-31",
        "release_year": 1999,
        "genres": ["Action", "Science Fiction"],
        "certification": "R",
        "rating": 8.2,
        "watch_providers": ["Max", "Netflix", "Amazon Prime Video"],
        "overview": "When a beautiful stranger leads computer hacker Neo to a forbidding underworld, he discovers the shocking truth--the life he knows is the elaborate deception of an evil cyber-intelligence.",
        "poster_path": "/lh4aVh0vOiHGwKkr1tFWR9v83Z5.jpg"
    },
    {
        "title": "Toy Story",
        "release_date": "1995-11-22",
        "release_year": 1995,
        "genres": ["Animation", "Adventure", "Comedy", "Family"],
        "certification": "G",
        "rating": 8.0,
        "watch_providers": ["Disney Plus"],
        "overview": "Led by Woody, Andy's toys live happily in his room until Andy's birthday brings Buzz Lightyear onto the scene. Afraid of losing his place in Andy's heart, Woody plots against Buzz.",
        "poster_path": "/uXDfjJbdP4ijW5hWSBrPrlK7VAu.jpg"
    },
    {
        "title": "Alien",
        "release_date": "1979-05-25",
        "release_year": 1979,
        "genres": ["Horror", "Science Fiction"],
        "certification": "R",
        "rating": 8.1,
        "watch_providers": ["Hulu", "Disney Plus"],
        "overview": "During its return journey, the commercial spacecraft Nostromo intercepts a distress signal from a distant planet. When a three-member team investigates, they discover a deadly lifeform.",
        "poster_path": "/vfrQk5IP3FIvVOLm6hiwEvm4lrC.jpg"
    },
    {
        "title": "Parasite",
        "release_date": "2019-05-30",
        "release_year": 2019,
        "genres": ["Thriller", "Drama", "Comedy"],
        "certification": "R",
        "rating": 8.5,
        "watch_providers": ["Max", "Hulu"],
        "overview": "All unemployed, Ki-taek's family takes peculiar interest in the wealthy and glamorous Parks for their livelihood until they get entangled in an unexpected incident.",
        "poster_path": "/7IiTTvv3n5EvX702h617n0o93Fv.jpg"
    },
    {
        "title": "Interstellar",
        "release_date": "2014-11-05",
        "release_year": 2014,
        "genres": ["Science Fiction", "Drama", "Adventure"],
        "certification": "PG-13",
        "rating": 8.4,
        "watch_providers": ["Paramount Plus", "Amazon Prime Video"],
        "overview": "The adventures of a group of explorers who make use of a newly discovered wormhole to surpass the limitations on human space travel and conquer the vast distances involved in an interstellar voyage.",
        "poster_path": "/gEU2QvHOmfg2eAc2v6fvRliovxI.jpg"
    },
    {
        "title": "Spirited Away",
        "release_date": "2001-07-20",
        "release_year": 2001,
        "genres": ["Animation", "Family", "Fantasy"],
        "certification": "PG",
        "rating": 8.5,
        "watch_providers": ["Max"],
        "overview": "A young girl, Chihiro, becomes trapped in a strange new world of spirits. When her parents undergo a mysterious transformation, she must call on the courage she never knew she had to free her family.",
        "poster_path": "/39wmItIWsg5sclI2L2qv4JDgq0R.jpg"
    },
    {
        "title": "The Dark Knight",
        "release_date": "2008-07-18",
        "release_year": 2008,
        "genres": ["Action", "Crime", "Drama", "Thriller"],
        "certification": "PG-13",
        "rating": 8.5,
        "watch_providers": ["Max", "Peacock"],
        "overview": "Batman raises the stakes in his war on crime. With the help of Lt. Jim Gordon and District Attorney Harvey Dent, Batman sets out to dismantle the remaining criminal organizations that plague the streets.",
        "poster_path": "/qJ2tWw3pmIMzZf65TYqgbw1TI3r.jpg"
    },
    {
        "title": "Pulp Fiction",
        "release_date": "1994-09-10",
        "release_year": 1994,
        "genres": ["Thriller", "Crime"],
        "certification": "R",
        "rating": 8.5,
        "watch_providers": ["Max", "Hulu", "Paramount Plus"],
        "overview": "A burger-loving hitman, his philosophical partner, a drug-addled gangster's moll, and a washed-up boxer converge in this sprawling, comedic crime caper. Their adventures unfurl in three stories.",
        "poster_path": "/d5iIlvFJmjeH4B0nQv1znAFGDQD.jpg"
    }
]

# --- TMDB Mapping Dictionaries ---
GENRE_MAP = {
    "action": 28, "adventure": 12, "animation": 16, "comedy": 35, "crime": 80,
    "documentary": 99, "drama": 18, "family": 10751, "fantasy": 14, "history": 36,
    "horror": 27, "music": 10402, "mystery": 9648, "romance": 10749, "science fiction": 878,
    "tv movie": 10770, "thriller": 53, "war": 10752, "western": 37
}

PROVIDER_MAP = {
    "netflix": 8,
    "amazon prime video": 9, "prime video": 9,
    "disney plus": 337, "disney+": 337,
    "hbo max": 1899, "max": 1899, "hbo": 1899,
    "hulu": 15,
    "apple tv plus": 350, "apple tv+": 350,
    "paramount plus": 531, "paramount+": 531,
    "peacock": 386, "peacock premium": 386
}


def _query_mock_database(
    genre: Optional[str],
    start_year: Optional[int],
    end_year: Optional[int],
    certification: Optional[str],
    watch_provider: Optional[str]
) -> List[Dict[str, Any]]:
    """Helper function to filter local mock database."""
    results = MOCK_MOVIES_DB
    
    if genre:
        genre_lower = genre.lower()
        results = [m for m in results if any(g.lower() == genre_lower for g in m["genres"])]
        
    if start_year:
        results = [m for m in results if m["release_year"] >= start_year]
        
    if end_year:
        results = [m for m in results if m["release_year"] <= end_year]
        
    if certification:
        cert_upper = certification.upper()
        results = [m for m in results if m["certification"].upper() == cert_upper]
        
    if watch_provider:
        wp_lower = watch_provider.lower()
        results = [
            m for m in results 
            if any(wp_lower in wp.lower() or wp.lower() in wp_lower for wp in m["watch_providers"])
        ]
        
    # Return formatted results
    formatted_results = []
    for m in results:
        formatted_results.append({
            "title": m["title"],
            "release_date": m["release_date"],
            "genres": m["genres"],
            "certification": m["certification"],
            "rating": m["rating"],
            "watch_providers": m["watch_providers"],
            "overview": m["overview"],
            "poster_path": f"https://image.tmdb.org/t/p/w500{m['poster_path']}" if m['poster_path'] else None,
            "source": "Local Mock Database"
        })
        
    return formatted_results


def _query_tmdb_api(
    genre: Optional[str],
    start_year: Optional[int],
    end_year: Optional[int],
    certification: Optional[str],
    watch_provider: Optional[str],
    api_key: str
) -> List[Dict[str, Any]]:
    """Helper function to query the real TMDB discover API."""
    url = "https://api.themoviedb.org/3/discover/movie"
    
    params = {
        "api_key": api_key,
        "language": "en-US",
        "sort_by": "popularity.desc",
        "certification_country": "US",
        "page": 1
    }
    
    # 1. Map Genre Name to Genre ID
    if genre:
        genre_id = GENRE_MAP.get(genre.lower())
        if genre_id:
            params["with_genres"] = str(genre_id)
        else:
            logger.warning(f"Genre '{genre}' could not be mapped to a TMDB ID.")
            
    # 2. Year Range
    if start_year:
        params["primary_release_date.gte"] = f"{start_year}-01-01"
    if end_year:
        params["primary_release_date.lte"] = f"{end_year}-12-31"
        
    # 3. Certification
    if certification:
        params["certification"] = certification.upper()
        
    # 4. Watch Provider
    if watch_provider:
        provider_id = PROVIDER_MAP.get(watch_provider.lower())
        if provider_id:
            params["with_watch_providers"] = str(provider_id)
            params["watch_region"] = "US"
        else:
            logger.warning(f"Watch Provider '{watch_provider}' could not be mapped to a TMDB ID.")

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        movies = data.get("results", [])
        formatted_results = []
        
        # We limit to top 8 results to keep context size manageable
        for m in movies[:8]:
            movie_id = m.get("id")
            
            # Default values if sub-calls fail
            detail_providers = [watch_provider] if watch_provider else []
            detail_certification = certification if certification else "N/A"
            
            if len(formatted_results) < 4 and movie_id:
                try:
                    # Fetch release dates (for certification) and watch providers
                    detail_url = f"https://api.themoviedb.org/3/movie/{movie_id}"
                    detail_params = {
                        "api_key": api_key,
                        "append_to_response": "release_dates,watch/providers"
                    }
                    detail_res = requests.get(detail_url, params=detail_params, timeout=5)
                    if detail_res.status_code == 200:
                        detail_data = detail_res.json()
                        
                        # Extract certification (US)
                        release_results = detail_data.get("release_dates", {}).get("results", [])
                        for country_data in release_results:
                            if country_data.get("iso_3166_1") == "US":
                                releases = country_data.get("release_dates", [])
                                for rel in releases:
                                    cert = rel.get("certification")
                                    if cert:
                                        detail_certification = cert
                                        break
                                break
                        
                        # Extract providers (US)
                        provider_results = detail_data.get("watch/providers", {}).get("results", {}).get("US", {})
                        providers_list = []
                        # Combine flatrate
                        for provider in provider_results.get("flatrate", []):
                            p_name = provider.get("provider_name")
                            if p_name and p_name not in providers_list:
                                providers_list.append(p_name)
                        if providers_list:
                            detail_providers = providers_list
                except Exception as ex:
                    logger.warning(f"Error fetching detail for movie {movie_id}: {ex}")
            
            # Map genre IDs back to names if possible
            inv_genre_map = {v: k.title() for k, v in GENRE_MAP.items()}
            movie_genres = [inv_genre_map.get(gid, f"Genre {gid}") for gid in m.get("genre_ids", [])]
            
            formatted_results.append({
                "title": m.get("title"),
                "release_date": m.get("release_date"),
                "genres": movie_genres,
                "certification": detail_certification,
                "rating": m.get("vote_average"),
                "watch_providers": detail_providers or ["Rent/Buy"],
                "overview": m.get("overview"),
                "poster_path": f"https://image.tmdb.org/t/p/w500{m.get('poster_path')}" if m.get("poster_path") else None,
                "source": "TMDB Live API"
            })
            
        return formatted_results
        
    except Exception as e:
        logger.error(f"Failed to query TMDB API: {e}. Falling back to mock database.")
        # Fall back automatically if API fails
        return _query_mock_database(genre, start_year, end_year, certification, watch_provider)


@tool
def discover_movies(query: str) -> str:
    """
    Search for movies based on filters. The input MUST be a valid JSON string containing the filters.
    
    Supported keys:
    - "genre": string, genre name (e.g. 'Horror', 'Action', 'Comedy', 'Science Fiction', 'Animation')
    - "start_year": integer, lower bound of release year (e.g., 1990)
    - "end_year": integer, upper bound of release year (e.g., 1999)
    - "certification": string, age rating certification (e.g., 'R', 'PG-13', 'PG', 'G')
    - "watch_provider": string, streaming platform (e.g., 'Netflix', 'Amazon Prime Video', 'Disney Plus', 'Hulu', 'Max')
    
    Example input: {"genre": "Horror", "start_year": 1990, "end_year": 1999, "certification": "R"}
    """
    logger.info(f"discover_movies received query string: {query}")
    
    # 1. Standardize and clean input
    cleaned_query = query.strip()
    if cleaned_query.startswith("```json"):
        cleaned_query = cleaned_query[7:]
    if cleaned_query.startswith("```"):
        cleaned_query = cleaned_query[3:]
    if cleaned_query.endswith("```"):
        cleaned_query = cleaned_query[:-3]
    cleaned_query = cleaned_query.strip()
    
    # Initialize parameters
    genre = None
    start_year = None
    end_year = None
    certification = None
    watch_provider = None
    
    # Try parsing JSON
    try:
        params = json.loads(cleaned_query)
        if isinstance(params, dict):
            genre = params.get("genre")
            start_year = params.get("start_year")
            end_year = params.get("end_year")
            certification = params.get("certification")
            watch_provider = params.get("watch_provider")
        else:
            genre = str(params)
    except Exception as e:
        logger.warning(f"Failed to parse query as JSON: {cleaned_query}. Error: {e}. Attempting regex/key-value parsing.")
        # Fallback regex/string parsing if LLM outputs text instead of JSON
        pairs = cleaned_query.replace("{", "").replace("}", "").split(",")
        for pair in pairs:
            if ":" in pair or "=" in pair:
                split_char = ":" if ":" in pair else "="
                parts = pair.split(split_char, 1)
                k = parts[0].strip().replace('"', '').replace("'", "").lower()
                v = parts[1].strip().replace('"', '').replace("'", "")
                
                if "genre" in k:
                    genre = v
                elif "start" in k or "gte" in k:
                    try: start_year = int(v)
                    except ValueError: pass
                elif "end" in k or "lte" in k:
                    try: end_year = int(v)
                    except ValueError: pass
                elif "cert" in k:
                    certification = v
                elif "provider" in k or "platform" in k or "watch" in k:
                    watch_provider = v

    logger.info(
        f"Parsed filters: genre={genre}, start_year={start_year}, end_year={end_year}, "
        f"certification={certification}, watch_provider={watch_provider}"
    )
    
    # Execute query
    api_key = settings.TMDB_API_KEY
    if api_key:
        logger.info("TMDB_API_KEY found, querying TMDB API...")
        results = _query_tmdb_api(genre, start_year, end_year, certification, watch_provider, api_key)
    else:
        logger.info("TMDB_API_KEY not found, using Local Mock Database...")
        results = _query_mock_database(genre, start_year, end_year, certification, watch_provider)
        
    if not results:
        return "No movies found matching these constraints. Try broadening your criteria."
        
    # Format the results into a string response for the agent to consume
    formatted_str_parts = []
    for idx, movie in enumerate(results, 1):
        genres_str = ", ".join(movie["genres"])
        providers_str = ", ".join(movie["watch_providers"])
        part = (
            f"Movie {idx}:\n"
            f"Title: {movie['title']}\n"
            f"Year: {movie['release_date'][:4]}\n"
            f"Genres: {genres_str}\n"
            f"Certification: {movie['certification']}\n"
            f"Rating: {movie['rating']}/10\n"
            f"Streaming on: {providers_str}\n"
            f"Poster URL: {movie['poster_path'] or 'None'}\n"
            f"Overview: {movie['overview']}\n"
        )
        formatted_str_parts.append(part)
        
    return "\n".join(formatted_str_parts)
