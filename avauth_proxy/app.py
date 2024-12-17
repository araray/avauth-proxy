from avauth_proxy import app

if __name__ == '__main__':
    # Run in debug mode for development. In production, run via gunicorn.
    app.run(host='0.0.0.0', port=5000, debug=True)
