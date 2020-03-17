from flask import current_app


def changedPasswordEmail(email, password):
    return """
                <!DOCTYPE html
  PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">

<head>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title></title>
  <link href="https://fonts.googleapis.com/css?family=Montserrat:400,700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="style.css">
  <style>
    *,
    ::after,
    ::before {
      box-sizing: border-box;
    }

    .row {
      display: -webkit-box;
      display: -ms-flexbox;
      display: flex;
      -ms-flex-wrap: wrap;
      flex-wrap: wrap;
      margin-right: -15px;
      margin-left: -15px;
    }

    u + #body a {
      color: inherit !important;
      text-decoration: none !important;
      font-size: inherit !important;
      font-family: inherit !important;
      font-weight: inherit !important;
      line-height: inherit !important;
    }
    
    body {
      font-family: 'Montserrat', sans-serif !important;
      Margin: 0;
      padding: 0;
      min-width: 100%;
      background-color: #ffffff;
    }
    

    table {
      border-spacing: 0;
    }

    td {
      padding: 0;
    }

    .position-relative {
      position: relative;
    }

    .outer {
      Margin: 0 auto;
      width: 100%;
      padding-top: 4rem;
      padding-bottom: 4rem;
      padding-right: 2rem;
      padding-left: 2rem;
    }

    .d-flex {
      display: flex;
    }

    .justify-content-center {
      justify-content: center;
    }

    .justify-content-end {
      justify-content: flex-end;
    }

    .main-bg {
      background-position: center;
      background-repeat: no-repeat;
      background-size: cover;
      background-image: url("""+current_app.config.get('SERVER_URL')+"""/resources/images/mailing/register-background.jpg);
    }

    .shadow {
      box-shadow: 0 .5rem 1rem rgba(0, 0, 0, .15);
    }

    .d-block-inline {
      display: inline-block;
    }

    .follow-us {
      font-weight: normal;
      font-size: 3rem;
      margin-top: 0rem;
      margin-bottom: 1rem;
    }

    .align-items-end {
      -ms-flex-align: end;
      align-items: flex-end;
      color: #122749;
    }

    @media (min-width: 0px) {
      .columns {
        width: 100%;
        /*padding-right: 15px;
          padding-left:  15px;
          -webkit-box-flex: 0;
          -ms-flex: 0 0 100%;
          flex: 0 0 100%;
          max-width: 100%;*/
      }

      .hand-paint {
        position: absolute;
        bottom: 80px;
        left: 0;
        display: none;
      }

      .container {
        position: relative;
        max-width: 1200px;
        padding-right: 15px;
        padding-left: 15px;
        width: 100%;
        padding-top: 4rem;
        padding-bottom: 4rem;
      }

      .title-welcome {
        font-size: 2rem;
        color: #FFF;
        width: 100%;
        font-weight: bold;
        margin-top: 0px;
        margin-bottom: 1.5rem;
        text-align: center;
      }

      .btn {
        border: 1px solid #FFF;
        font-size: 1.3rem;
        padding: 1rem 2rem 1rem 2rem;
        background-color: transparent;
        color: #FFF;
        font-weight: normal;
      }

      .wrapper {
        background-color: rgba(0, 127, 159, 0.9019607843137255);
        padding: 1rem 2rem 5rem 1rem;
        box-shadow: 0 .5rem 1rem rgba(0, 0, 0, .15);
      }

      .text {
        color: #FFF;
        font-size: 1.3rem;
        text-align: center;
      }

      .text-2 {
        color: #FFF;
        font-size: 1.3rem;
        text-align: left;
      }

      .wrapper-btn {
        width: 100%;
        text-align: center;
        margin-top: 3rem;
      }

      .social-wrapper {
        margin-top: 2rem;
        width: 100%;
        text-align: center;
      }

      ul {
        list-style: none;
        padding: 0px;
        text-align: center;
      }

      ul li img {
        width: 3rem;
      }
    }

    @media (min-width: 320px) {
      .outer {
        max-width: auto;
      }
    }

    @media (min-width: 576px) {
      .outer {
        max-width: auto;
      }
    }

    @media (min-width: 720px) {
      .outer {
        max-width: 720px;
      }
    }

    @media (min-width: 992px) {
      .outer {
        max-width: 800px;
      }

      .columns {}

      .social-wrapper {
        order: 0;
        width: auto;
      }

      .hand-paint {
        display: inherit;
        width: auto;
      }

      .title-welcome {
        font-size: 2.5rem;
      }

      .container {
        padding-right: 3rem;
      }

      .btn {
        padding: 1rem 2rem 1rem 2rem;
      }

      .wrapper {
        padding: 3rem 3rem 10rem 2rem;
      }
    }

    @media (min-width: 1200px) {
      .hand-paint {
        width: 20rem;
      }
    }
  </style>
</head>

<body id="body">
  <center>
    <table class="outer main-bg shadow" width="100%">
      <tr>
        <td style="width: 100%;">
          <div class="columns">
            <div class="wrapper">
              <h3 class="title-welcome">Cambio de contraseña</h3>
              <p class="text">Inicia sesión usando las siguientes credenciales:
              </p>
              <div class="justify-content-left">
                <p class="text-2"><b>Email: </b>"""+email+"""</p>
                <p class="text-2"><b>Password: </b>"""+password+"""</p>
              </div>

              <div class="wrapper-btn">
                <button class="btn">Ir a AmbLeMa</button>
              </div>
            </div>
          </div>
        </td>
      </tr>

    </table>
  </center>
</body>

</html>
                """
