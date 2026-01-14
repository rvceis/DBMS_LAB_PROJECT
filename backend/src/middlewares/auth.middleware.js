import  jwt from "jsonwebtoken";
import { apierror } from "../utils/ApiError.js";
import { asyncHandler } from "../utils/AsyncHandler.js";


export const verifyJwt = asyncHandler(
    async (req,res,next)=>{
        try {
            const token =  req.cookies?.AccessToken || req.header("authorization")?.replace('Bearer ', "")
            if(!token)
                throw new apierror(401,"unothorized request")
            const decoded=jwt.verify(token,process.env.ACCESS_TOKEN_SECRET)
            const user = await User.findById(decoded?._id).select("-password -refreshToken")
            if(!user)
                throw new apierror(401,"Invalid Access Token ")
    
            req.user=user;
            next();
        } catch (error) {
            throw new apierror(400,'invalid Access Token')
        }
    } 
)