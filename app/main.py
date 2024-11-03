import re

from fastapi import FastAPI, Request, Depends, HTTPException, Query, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from authlib.integrations.starlette_client import OAuth, OAuthError
from starlette.middleware.sessions import SessionMiddleware
from starlette.config import Config
from sqlalchemy.orm import Session

from datetime import datetime

from .middleware import LanguageMiddleware
from .database import engine, get_db
from . import models, crud, email
from .i18n import _

faculty_dict = {
    16: "Faculty of Naval Architecture and Maritime",
    10: "Faculty of Civil Engineering",
    3: "Faculty of Chemical and Metallurgical Engineering",
    18: "Institute of Clean Energy Technologies",
    1: "Rectorate",
    2: "Faculty of Architecture",
    4: "Faculty of Mechanical Engineering",
    5: "Institute of Science and Technology",
    6: "Institute of Social Sciences",
    7: "Vocational School",
    8: "Faculty of Electrical and Electronics Engineering",
    9: "Faculty of Arts and Sciences",
    11: "Faculty of Economics and Administrative Sciences",
    12: "Faculty of Art and Design",
    13: "School of Foreign Languages",
    14: "Faculty of Education",
    23: "Faculty of Applied Sciences",
    15: "National Palaces and Historical Buildings Vocational School"
}

faculty_dict_tr = {
    16: "Gemi İnşaatı ve Denizcilik Fakültesi",
    10: "İnşaat Fakültesi",
    3: "Kimya-Metalurji Fakültesi",
    18: "Temiz Enerji Teknolojileri Enstitüsü",
    1: "Rektörlük",
    2: "Mimarlık Fakültesi",
    4: "Makine Fakültesi",
    5: "Fen Bilimleri Enstitüsü",
    6: "Sosyal Bilimler Enstitüsü",
    7: "Meslek Yüksekokulu",
    8: "Elektrik-Elektronik Fakültesi",
    9: "Fen-Edebiyat Fakültesi",
    11: "İktisadi ve İdari Bilimler Fakültesi",
    12: "Sanat ve Tasarım Fakültesi",
    13: "Yabancı Diller Yüksekokulu",
    14: "Eğitim Fakültesi",
    23: "Uygulamalı Bilimler Fakültesi",
    15: "Milli Saraylar ve Tarihi Yapılar Meslek Yüksekokulu"
}

# Load environment variables
config = Config('.env')
GOOGLE_CLIENT_ID = config('GOOGLE_CLIENT_ID', cast=str)
GOOGLE_CLIENT_SECRET = config('GOOGLE_CLIENT_SECRET', cast=str)
SECRET_KEY = config('SECRET_KEY', cast=str)

# OAuth setup
oauth = OAuth()
oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")
app.add_middleware(LanguageMiddleware, templates=templates)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

models.Base.metadata.create_all(bind=engine)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    user = request.session.get('user')
    top_professors = crud.get_leaderboard_data(db)[:5]  # Get top 5 professors
    recent_reviews = crud.get_recent_reviews(db)  # Get recent reviews
    return templates.TemplateResponse("home.html", {
        "request": request,
        "user": user,
        "top_professors": top_professors,
        "recent_reviews": recent_reviews
    })

@app.get("/robots.txt")
async def robots():
    return Response(content="User-agent: *\nAllow: /", media_type="text/plain")

@app.get("/sitemap.xml")
async def sitemap():
    return Response(content="""<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url><loc>https://rateyuprofessors.com/</loc></url>
        <url><loc>https://rateyuprofessors.com/teachers</loc></url>
        <url><loc>https://rateyuprofessors.com/leaderboard</loc></url>
        <url><loc>https://rateyuprofessors.com/faculty</loc></url>
    </urlset>""", media_type="application/xml")

@app.get("/favicon.ico")
async def favicon():
    return Response(content=open("static/favicon.ico", "rb").read(), media_type="image/x-icon")

@app.get("/privacy", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})

@app.post("/set-lang/{lang}")
async def set_language(lang: str, request: Request, response: Response):
    if lang not in ['en', 'tr']:
        raise HTTPException(status_code=400, detail="Invalid language. Only 'en' and 'tr' are supported.")
    request.session['language'] = lang
    referer = request.headers.get('Referer')
    response = RedirectResponse(referer or "/")
    return response

@app.get("/login")
async def login(request: Request):
    redirect_uri = request.url_for('auth')
    return await oauth.google.authorize_redirect(request, redirect_uri) # type: ignore

@app.get("/account", response_class=HTMLResponse)
async def account(request: Request, db: Session = Depends(get_db)):
    user = request.session.get('user')
    if user:
        db_user = crud.get_user_by_email(db, user['email'])
        if db_user:
            user['admin'] = db_user.admin
            user['verified'] = db_user.verified
            user['student_email'] = db_user.student_email
    return templates.TemplateResponse("account.html", {"request": request, "user": user})

@app.get("/auth")
async def auth(request: Request, db: Session = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request) # type: ignore
    except OAuthError as error:
        return HTMLResponse(f"<h1>OAuth Error</h1><p>{str(error)}</p>")

    user_info = token.get('userinfo')
    if user_info:
        google_id = user_info['sub']
        email = user_info['email']

        db_user = crud.get_user_by_google_id(db, google_id)
        if db_user:
            # Update existing user
            crud.update_user(db, db_user, {
                'full_name': user_info.get('name'),
                'picture': user_info.get('picture'),
                'locale': user_info.get('locale')
            })
        else:
            # Create new user
            crud.create_user(db, {
                'full_name': user_info.get('name'),
                'gmail': email,
                'google_id': google_id,
                'picture': user_info.get('picture'),
                'locale': user_info.get('locale')
            })

        request.session['user'] = {
            'name': user_info.get('name'),
            'email': email,
            'picture': user_info.get('picture')
        }

    return HTMLResponse(
        "<script>window.opener.postMessage('login_success', '*'); window.close();</script>"
    )

@app.get("/logout")
async def logout(request: Request):
    request.session.pop('user', None)
    return HTMLResponse("""
    <div id="login-status">
        <p>You have been logged out.</p>
        <button onclick="openLoginPopup()">Login with Google</button>
    </div>
    <script>
    function openLoginPopup() {
        window.open('/login', 'Login', 'width=600,height=600');
    }
    </script>
    """)

@app.get("/verify", response_class=HTMLResponse)
async def verify_page(request: Request):
    user = request.session.get('user')
    return templates.TemplateResponse("verify.html", {"request": request, "user": user})

@app.post("/verify", response_class=HTMLResponse)
async def verify_email(request: Request, db: Session = Depends(get_db), student_email: str = Form(...)):
    user = request.session.get('user')
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Check if the email is a valid Yildiz student email
    if not re.match(r"^[a-zA-Z0-9._%+-]+@std\.yildiz\.edu\.tr$", student_email):
        return templates.TemplateResponse("verify.html", {"request": request, "user": user, "error": "Invalid Yildiz student email"})

    # Check if the email is already used
    existing_user = crud.get_user_by_student_email(db, student_email)
    if existing_user and existing_user.verified:
        return templates.TemplateResponse("verify.html", {"request": request, "user": user, "error": "This student email is already verified"})

    db_user = crud.get_user_by_email(db, user['email'])
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    verification_code = crud.set_verification_code_email(db, db_user, student_email)
    email.send_verification_email(student_email, verification_code)

    return templates.TemplateResponse("verify.html", {"request": request, "user": user, "message": "Verification code sent to your student email"})

@app.post("/verify/code", response_class=HTMLResponse)
async def verify_code(request: Request, db: Session = Depends(get_db), verification_code: str = Form(...)):
    user = request.session.get('user')
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    db_user = crud.get_user_by_email(db, user['email'])
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if user has exceeded maximum attempts
    if db_user.verification_attempts >= 5:
        return templates.TemplateResponse("verify.html", {
            "request": request,
            "user": user,
            "error": "Maximum verification attempts exceeded. Please request a new code."
        })

    # Verify the code
    if db_user.verification_code != verification_code:
        crud.increment_verification_attempts(db, db_user)
        remaining_attempts = 5 - db_user.verification_attempts
        return templates.TemplateResponse("verify.html", {
            "request": request,
            "user": user,
            "error": f"Invalid verification code. {remaining_attempts} attempts remaining."
        })

    if db_user.verification_code_expires < datetime.utcnow():
        return templates.TemplateResponse("verify.html", {
            "request": request,
            "user": user,
            "error": "Verification code expired"
        })

    crud.verify_user(db, db_user, str(db_user.student_email))
    user['verified'] = True
    user['student_email'] = db_user.student_email
    request.session['user'] = user

    return templates.TemplateResponse("verify.html", {
        "request": request,
        "user": user,
        "message": "Email verified successfully"
    })

@app.get("/teachers", response_class=HTMLResponse)
async def list_professors(request: Request, db: Session = Depends(get_db)):
    user = request.session.get('user')
    professors = crud.get_all_professors(db)
    return templates.TemplateResponse("teachers.html", {"request": request, "user": user, "professors": professors})

@app.get("/teachers/info/{professor_id}", response_class=HTMLResponse)
async def professor_detail(request: Request, professor_id: int, db: Session = Depends(get_db)):
    user = request.session.get('user')
    professor = crud.get_professor(db, professor_id)
    if not professor:
        raise HTTPException(status_code=404, detail="Professor not found")

    ratings = crud.get_professor_ratings(db, professor_id)
    avg_ratings = crud.get_professor_average_ratings(db, professor_id)

    user_rating = None
    if user:
        db_user = crud.get_user_by_email(db, user['email'])
        user_rating = crud.get_user_rating_for_professor(db, db_user.id, professor_id)

    return templates.TemplateResponse("teacher_detail.html", {
        "request": request,
        "user": user,
        "professor": professor,
        "ratings": ratings,
        "avg_ratings": avg_ratings,
        "user_rating": user_rating
    })

@app.get("/teachers/search", response_class=HTMLResponse)
async def search_professors(request: Request, db: Session = Depends(get_db), q: str = Query(None)):
    user = request.session.get('user')
    if q:
        professors = crud.search_professors(db, q)
    else:
        professors = crud.get_all_professors(db)
    return templates.TemplateResponse("teachers.html", {"request": request, "user": user, "professors": professors, "search_query": q})

@app.post("/teachers/{professor_id}/rate")
async def rate_professor(
    request: Request,
    professor_id: int,
    db: Session = Depends(get_db),
    comment: str = Form(default=""),
    english_proficiency: int = Form(...),
    friendliness: int = Form(...),
    knowledge: int = Form(...)
):
    user = request.session.get('user')
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    db_user = crud.get_user_by_email(db, user['email'])
    existing_rating = crud.get_user_rating_for_professor(db, db_user.id, professor_id)

    if not user.get('verified'): comment = ""

    if existing_rating:
        crud.update_rating(db, existing_rating.id, comment, english_proficiency, friendliness, knowledge)
    else:
        crud.create_rating(db, db_user.id, professor_id, comment, english_proficiency, friendliness, knowledge)

    return RedirectResponse(url=f"/teachers/info/{professor_id}", status_code=303)

@app.post("/teachers/{professor_id}/ratings/{rating_id}/delete")
async def delete_rating(
    request: Request,
    professor_id: int,
    rating_id: int,
    db: Session = Depends(get_db)
):
    user = request.session.get('user')
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    db_user = crud.get_user_by_email(db, user['email'])
    rating = crud.get_rating(db, rating_id)

    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")

    if rating.user_id != db_user.id and not db_user.admin:
        raise HTTPException(status_code=403, detail="Not authorized to delete this rating")

    crud.delete_rating(db, rating_id)

    return RedirectResponse(url=f"/teachers/info/{professor_id}", status_code=303)


# Leaderboard

@app.get("/leaderboard", response_class=HTMLResponse)
async def leaderboard(request: Request, db: Session = Depends(get_db)):
    user = request.session.get('user')
    leaderboard_data = crud.get_leaderboard_data(db)
    return templates.TemplateResponse("leaderboard.html", {"request": request, "user": user, "leaderboard_data": leaderboard_data})


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return HTMLResponse(f"<h1>Error {exc.status_code}</h1><p>{exc.detail}</p>")


# Faculties

@app.get("/faculty/{faculty_id}", response_class=HTMLResponse)
async def list_faculty_professors(request: Request, faculty_id: int, db: Session = Depends(get_db)):
    user = request.session.get('user')

    if faculty_id not in faculty_dict:
        raise HTTPException(status_code=404, detail="Faculty not found")

    professors = crud.get_professors_by_faculty(db, faculty_id)
    faculty_name = faculty_dict[faculty_id] if request.session['language']== 'en' else faculty_dict_tr[faculty_id]
    return templates.TemplateResponse("faculty_professors.html", {
        "request": request,
        "user": user,
        "professors": professors,
        "faculty_name": faculty_name,
        "faculty_id": faculty_id
    })

@app.get("/faculty", response_class=HTMLResponse)
async def list_faculties(request: Request):
    user = request.session.get('user')

    return templates.TemplateResponse("faculties.html", {
        "request": request,
        "user": user,
        "faculties": faculty_dict if request.session['language']== 'en' else faculty_dict_tr

    })

@app.get("/faculty/{faculty_id}/leaderboard", response_class=HTMLResponse)
async def faculty_leaderboard(request: Request, faculty_id: int, db: Session = Depends(get_db)):
    user = request.session.get('user')

    if faculty_id not in faculty_dict:
        raise HTTPException(status_code=404, detail="Faculty not found")

    faculty_name = faculty_dict[faculty_id] if request.session['language']== 'en' else faculty_dict_tr[faculty_id]
    leaderboard_data = crud.get_faculty_leaderboard_data(db, faculty_id)

    return templates.TemplateResponse("faculty_leaderboard.html", {
        "request": request,
        "user": user,
        "faculty_name": faculty_name,
        "leaderboard_data": leaderboard_data
    })

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse(
        "404.html",
        {"request": request, "user": request.session.get('user')},
        status_code=404
    )

@app.exception_handler(500)
async def server_error_handler(request: Request, exc: Exception):
    return templates.TemplateResponse(
        "500.html",
        {"request": request, "user": request.session.get('user')},
        status_code=500
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 404:
        return await not_found_handler(request, exc)
    return templates.TemplateResponse(
        "500.html",
        {
            "request": request,
            "user": request.session.get('user'),
        },
        status_code=exc.status_code
    )
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
