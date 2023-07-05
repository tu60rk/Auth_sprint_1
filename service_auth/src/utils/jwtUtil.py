# from datetime import datetime, timedelta

# import jwt
# # from jose import jwt
# from fastapi import APIRouter, Depends, HTTPException, Query

# from . import constantUtil


# async def create_access_token(*, data: dict, expires_delta: timedelta = None):
# 	to_encode = data.copy()
# 	if expires_delta:
# 		expire = datetime.utcnow() + expires_delta
# 	else:
# 		expire = datetime.utcnow() + timedelta(minutes=constantUtil.ACCESS_TOKEN_EXPIRE_MINUTE)
# 	to_encode.update({"exp": expire})
# 	return jwt.encode(to_encode, constantUtil.SECRET_KEY, algorithm=constantUtil.ALGORYTHM_HS256)


# def create_refresh_token(*, data: dict, expires_delta: timedelta = None):
# 	to_encode = data.copy()
# 	if expires_delta:
# 		expire = datetime.utcnow() + expires_delta
# 	else:
# 		expire = datetime.utcnow() + timedelta(minutes=constantUtil.REFRESH_TOKEN_EXPIRE_DAYS)
# 	to_encode.update({"exp": expire})
# 	return jwt.encode(to_encode, constantUtil.SECRET_KEY, algorithm=constantUtil.ALGORYTHM_HS256)


# def decode_token(token: str):
# 	try:
# 		payload = jwt.decode(token, constantUtil.SECRET_KEY, algorithms=[constantUtil.ALGORYTHM_HS256])
# 		return payload
# 	except jwt.ExpiredSignatureError:
# 		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
# 	except jwt.InvalidTokenError:
# 		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
