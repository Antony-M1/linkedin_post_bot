# InvalidCookieDomainException
**selenium.common.exceptions.InvalidCookieDomainException: Message: invalid cookie domain**

After running the script for 14+ hours in scheduler mode with Interval period of `1 Hour` I'm getting this exception. based on the log at the 15th iteration of scheduler job its failed.
```py
Traceback (most recent call last):
  File "/home/softsuave/_practice/test_task/linkedIn_post_bot/venv/lib/python3.10/site-packages/apscheduler/executors/base.py", line 125, in run_job
    retval = job.func(*job.args, **job.kwargs)
  File "/home/softsuave/_practice/test_task/linkedIn_post_bot/post_bot.py", line 326, in schedule_post_bot
    bot.login()
  File "/home/softsuave/_practice/test_task/linkedIn_post_bot/post_bot.py", line 100, in login
    self.driver.add_cookie(cookie)
  File "/home/softsuave/_practice/test_task/linkedIn_post_bot/venv/lib/python3.10/site-packages/selenium/webdriver/remote/webdriver.py", line 641, in add_cookie
    self.execute(Command.ADD_COOKIE, {"cookie": cookie_dict})
  File "/home/softsuave/_practice/test_task/linkedIn_post_bot/venv/lib/python3.10/site-packages/selenium/webdriver/remote/webdriver.py", line 354, in execute
    self.error_handler.check_response(response)
  File "/home/softsuave/_practice/test_task/linkedIn_post_bot/venv/lib/python3.10/site-packages/selenium/webdriver/remote/errorhandler.py", line 229, in check_response
    raise exception_class(message, screen, stacktrace)
selenium.common.exceptions.InvalidCookieDomainException: Message: invalid cookie domain
```

The `InvalidCookieDomainException` in Selenium is raised when attempting to add cookies that don’t match the current domain of the browser session. This typically happens if the session has either navigated to a different domain or was restarted without re-authenticating, making any previously saved cookies invalid for the new session.

Here are some likely causes and preventive solutions:

### Causes
1. **Session Expiry or Reset**: After 14+ hours, your session may have expired, or the browser may have restarted, clearing the session.
2. **Domain Mismatch**: The cookies being added might not match the domain that the browser is currently visiting.
3. **Session Not Persistent**: If the Selenium driver restarts, the session and cookies won’t persist, causing a mismatch with stored cookies.

### Solutions
To prevent this error and improve stability over long intervals, consider the following practices:

1. **Re-authenticate Each Session**: Avoid relying solely on cookies for re-authentication if you restart the browser. Set up a fresh login at each interval to ensure a valid session.
   
   ```python
   if not self.driver.current_url.startswith("https://www.linkedin.com"):
       self.driver.get("https://www.linkedin.com/login")
   ```

2. **Check Domain Before Adding Cookies**: Ensure the domain matches before setting cookies. This can be done by navigating to the intended domain before adding cookies.

   ```python
   # Navigate to LinkedIn's home page before adding cookies
   self.driver.get("https://www.linkedin.com")
   ```

3. **Refresh Cookies Periodically**: If cookies have an expiry time, retrieve fresh cookies periodically and store them securely.

4. **Use a Persistent Storage Mechanism**: Instead of manually adding cookies, you can use Selenium’s `driver.get_cookies()` and `driver.add_cookie()` to save and load cookies from a file.

   ```python
   # Saving cookies to a file
   with open("cookies.pkl", "wb") as file:
       pickle.dump(self.driver.get_cookies(), file)

   # Loading cookies
   with open("cookies.pkl", "rb") as file:
       for cookie in pickle.load(file):
           self.driver.add_cookie(cookie)
   ```

5. **Run Session Checks Before Each Interval**: Before executing scheduled tasks, verify that the domain and cookies are still valid. If not, re-initiate the login sequence.

6. **Error Handling**: Implement robust error handling to catch this exception and trigger a re-authentication.

By ensuring domain consistency, refreshing cookies regularly, and re-authenticating sessions as needed, you can avoid errors like `InvalidCookieDomainException` over long-running sessions.