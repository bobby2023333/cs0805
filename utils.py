@app.route('/analyze')
@login_required
def analyze():
    # Get the current user's uploads
    uploads = UserUpload.query.filter_by(user_id=current_user.id).all()

    # Process the filenames
    for upload in uploads:
        upload.filename = process_filename(upload.filename)

    # Commit changes to the database
    db.session.commit()

    return render_template('analyze.html', uploads=uploads)


