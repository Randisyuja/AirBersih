<!doctype html>
<html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Air Bersih - Login Page</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-4bw+/aepP/YC94hEpVNVgiZdgIC5+VKNBQNGCHeKRQN+PtmoHDEXuppvnDJzQIu9" crossorigin="anonymous">
        <style>
            .fontnih{
                color:white;
                font-family:inter;
                margin-bottom:15px;
            }
        </style>
    </head>
    <body style="background-color:rgba(81,133,76,255)">
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/js/bootstrap.bundle.min.js" integrity="sha384-HwwvtgBNo3bZJJLYd8oVXjrBZt8cqVSpeBNS5n7C8IVInixGAoxmnlMuBnhbgrkm" crossorigin="anonymous"></script>
        <div class="container text-center" style="margin:90px auto;">
            <div class="row">
                <div class="col">
                    <h1 style="font-family:inter; color:black; padding-top:25px; padding-right:20px; text-align:center; font-weight:900;"><i>AIR BERSIH</i></h1>
                </div>
                <div class="col" style="background-color:rgba(58,97,54,255); border-radius:25px; padding:3rem">
                    <div class="container text-center">
                        <div class="row">
                            <div class="col">
                                <h2 style="color:white; text-align:center; font-family:inter; font-weight:bolder;"><i>LOGIN</i></h2>
                            </div>
                            <div class="col-5">
                            </div>
                            <div class="col">
                            </div>
                        </div>
                    </div>
                    <form class="px-4 py-3" action="" method="post">
                        <div class="form-group" align="left" style="margin-bottom:15px;">
                            <label class="fontnih">Id</label>
                            <input type="text" class="form-control" id="exampleDropdownFormEmail1" placeholder="ID" name="id">
                        </div>
                        <div class="form-group" align="left" style="margin-bottom:15px;">
                            <label class="fontnih">Password</label>
                            <input type="password" class="form-control" id="exampleDropdownFormPassword1" placeholder="Password" name="password">
                        </div>
                        <div class="form-group" style="padding-bottom:5px" align="left">
                            <a class="fontnih" href="#" style="text-decoration:none;">
                            Forgot password ?
                            </a>
                        </div>
                        <div class="form-row">
                            <span align="left">
                                <button style="width:45%; margin-right: 20px;" type="submit" class="btn btn-primary" name="submit">Sign in</button>
                            </span>
                            <span>
                                <button style="width:45%; margin-left: 20px;" type="submit" class="btn btn-primary" name="submit">Sign in</button>
                            </span>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </body>
</html>