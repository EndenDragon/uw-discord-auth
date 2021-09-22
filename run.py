from uwdiscord.app import app
import os

if __name__ == "__main__":
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run(host="0.0.0.0", port=3000, debug=True)
