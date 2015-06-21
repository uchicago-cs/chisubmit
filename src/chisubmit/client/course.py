#  Copyright (c) 2013-2014, The University of Chicago
#  All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#
#  - Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
#  - Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
#  - Neither the name of The University of Chicago nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
#  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
#  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
#  SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
#  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
#  CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
#  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
#  POSSIBILITY OF SUCH DAMAGE.

from chisubmit.client.types import ChisubmitAPIObject, Attribute, AttributeType

class Course(ChisubmitAPIObject):
    
    url = Attribute(name="url", 
                    attrtype=AttributeType.STRING, 
                   patchable=False)    
    
    shortname = Attribute(name="shortname", 
                   attrtype=AttributeType.STRING, 
                   patchable=True)
    
    name = Attribute(name="name", 
                     attrtype=AttributeType.STRING, 
                     patchable=True)
    
    git_usernames = Attribute(name="git_usernames", 
                              attrtype=AttributeType.STRING, 
                              patchable=True)
    
    git_staging_usernames = Attribute(name="git_staging_usernames", 
                                      attrtype=AttributeType.STRING, 
                                      patchable=True)

    extension_policy = Attribute(name="extension_policy", 
                                 attrtype=AttributeType.STRING, 
                                 patchable=True)

    default_extensions = Attribute(name="default_extensions", 
                                   attrtype=AttributeType.INTEGER, 
                                   patchable=True)



