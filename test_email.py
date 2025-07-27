import smtplib
server = smtplib.SMTP("smtp.gmail.com", 587)
server.starttls()
server.login("judeaio120@gmail.com", "evwb phml zpgy nphu")
print("Login successful")
server.quit()