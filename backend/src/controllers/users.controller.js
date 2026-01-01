import {prisma} from "../db config/prisma.js"

export const createUser = async(req,res)=>{
    const {email,role,name}=req.body;
    if(!email || !role || !name)
    {
        throw new console.log("Emial, role , name is missing or undefined!\n",email,role,name);
        return res.json({
            message:"Provide correct credentials!"
        })

        const user=await prisma.users.create(
            {
                data:{name,email,role}
            }
        )

        
    }

}