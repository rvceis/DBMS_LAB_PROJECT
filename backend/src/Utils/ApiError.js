class apierror extends Error{
    constructor(
        code=500,
        message='something went wrong',
        errors=[]){
            super(message)
            this.message=message
            this.code=code
            this.data=null
            this.errors=errors
            this.success=false
    }   
}

export {apierror}